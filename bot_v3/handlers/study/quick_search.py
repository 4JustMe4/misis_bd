from aiogram import Router, types, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from typing import Union
from typing import List
import logging
import re

from .common import loadData, user_selections, get_day
from .current_schedule import get_schedule


from handlers.keyboards import (
    get_weekday_buttons,
    get_room_weekday_buttons,
    get_full_schedule_menu,
    get_institutes_menu,
    get_class_schedule_menu,
    get_teacher_weekday_buttons
)


router = Router()



def detect_and_search(query: str) -> dict:
    """Улучшенный поиск с логированием"""
    query = query.strip().upper()
    result = {"type": None, "matches": []}
    
    #print(f"\n=== DEBUG: Поиск '{query}' ===")  # Отладочный вывод
    
    # 1. Поиск преподавателя (только буквы)
    if query.isalpha():
        #print("Тип: Проверка преподавателя")
        teachers = loadData("teacher").keys()
        
        matches = [t for t in teachers if t.split()[0].upper().startswith(query)]
        if matches:
            #print(f"Найдено преподавателей: {len(matches)}")
            return {"type": "teacher", "matches": sorted(matches)}
    
    # 2. Поиск групп (формат: БУТ-21-1)
    if re.match(r'^[А-ЯA-Z]{2,}(-\d{2,})?(-\d)?$', query):
        #print("Тип: Проверка группы")
        all_groups = loadData("schedule").keys()
        
        # Нормализуем запрос (БПМ 21-1 → БПМ-21-1)
        normalized = normalize_group_name(query)
        #print(f"Нормализованная группа: {normalized}")
        
        # Ищем точные и частичные совпадения
        matches = [g for g in all_groups if g.startswith(normalized)]
        if matches:
            #print(f"Найдено групп: {len(matches)}")
            return {"type": "group", "matches": sorted(matches)}
    
    # 3. Поиск аудиторий (формат: Л-711 или Л711)
    #print("Тип: Проверка аудитории")
    all_rooms = loadData("location").keys()
    
    # Нормализуем запрос (л711 → Л-711)
    normalized = normalize_room_name(query)
    #print(f"Нормализованная аудитория: {normalized}")
    
    # Ищем точные и варианты без дефиса
    matches = [
        r for r in all_rooms 
        if normalize_room_name(r) == normalized 
        or r.replace("-", "") == normalized.replace("-", "")
    ]
    
    if matches:
        #print(f"Найдено аудиторий: {len(matches)}")
        return {"type": "room", "matches": sorted(matches)}
    
    #print("Ничего не найдено")
    return {"type": None, "matches": []}



# Обработчик выбора типа расписания (группы/преподаватели/аудитории)
@router.callback_query(F.data.startswith("full_"))
async def handle_full_schedule_choice(call: CallbackQuery):
    choice = call.data.split("_")[1]
    
    if choice == "group":
        await call.message.edit_text(
            "Выберите институт:",
            reply_markup=get_institutes_menu()
        )
    elif choice == "teacher":
        await call.message.edit_text(
            "Введите фамилию преподавателя:",
            reply_markup=None
        )
    elif choice == "room":
        await call.message.edit_text(
            "Введите номер аудитории (например: Л711, Б-123):",
            reply_markup=None
        )
    elif choice == "back":
        await call.message.edit_text(
            "Выберите тип расписания:",
            reply_markup=get_class_schedule_menu()
        )


def get_room_schedule(room: str, week_type: str, day: str, schedule: dict) -> str:
    #Формирует отформатированное расписание для аудитории#
    if room not in schedule:
        return "Аудитория не найдена в расписании 🤔"
    
    response = f"<b>Расписание занятий в аудитории {room}</b>\n"
    response += f"{day}, {'верхняя' if week_type == 'upper' else 'нижняя'} неделя:\n\n"
    
    times = {
        "1": "9:00-10:35", "2": "10:50-12:25", "3": "12:40-14:15",
        "4": "14:30-16:05", "5": "16:20-17:55", "6": "18:00-19:25", "7": "19:35-21:00"
    }
    
    if day not in schedule[room]:
        return f"{response}Занятий нет 🥳"
    
    pairs_info = []
    for pair_num, pair_data in schedule[room][day].items():
        week_data = pair_data.get(week_type, {}).get("subjects", {})
        
        for subject, subject_data in week_data.items():
            subject_name, *teacher = subject.split("\n")
            teacher = teacher[0] if teacher else ""
            
            groups = []
            for group, group_data in subject_data.get("groups", {}).items():
                subgroups = group_data.get("subGroups", [])
                groups.append(f"{group} [{', '.join(subgroups)}]")
            
            if groups:
                pairs_info.append({
                    "num": pair_num,
                    "time": times.get(pair_num, ""),
                    "subject": subject_name,
                    "teacher": teacher,
                    "groups": "\n".join(groups)
                })
    
    if pairs_info:
        for pair in sorted(pairs_info, key=lambda x: x["num"]):
            response += (
                f"{pair['num']} пара ({pair['time']})\n"
                f"<b>{pair['subject']}</b>\n"
            )
            if pair["teacher"]:
                response += f"{pair['teacher']}\n"
            response += f"{pair['groups']}\n\n"
    else:
        response += "Занятий нет 🥳\n"
    
    response += f"Сегодня {day}, {'верхняя' if week_type == 'upper' else 'нижняя'} неделя"
    return response


# Хэндлеры
@router.message(F.text)
async def handle_quick_search(message: Message):
    """Универсальный обработчик поиска для всех типов запросов"""
    query = message.text.strip()
    
    # 1. Сначала проверяем преподавателей (только буквы)
    if query.isalpha():
        teachers = find_teachers_by_last_name(query)
        
        if not teachers:
            await message.answer("🔍 Преподаватели не найдены")
            return
            
        buttons = [
            [InlineKeyboardButton(
                text=teacher,
                callback_data=f"teacher_select_{teacher}"
            )]
            for teacher in teachers[:5]  # Ограничиваем 5 вариантами
        ]
        
        await message.answer(
            "🔍 Найденные преподаватели:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
        return
    
    # 2. Если не только буквы - обрабатываем как группу/аудиторию
    search_result = detect_and_search(query)
    
    if not search_result["matches"]:
        await message.answer(
            "❌ Ничего не найдено. Проверьте формат:\n"
            "• Группа: <code>БПМ-21-1</code> или <code>БПМ-21</code>\n"
            "• Аудитория: <code>Л-711</code> или <code>Л711</code>\n"
            "• Преподаватель: <code>Иванов</code>",
            parse_mode="HTML"
        )
        return
    
    # 3. Обработка групп и аудиторий
    if search_result["type"] == "group":
        if len(search_result["matches"]) == 1:
            await show_group_schedule(message, search_result["matches"][0], "all")
        else:
            buttons = [
                [InlineKeyboardButton(
                    text=group,
                    callback_data=f"quick_group_{group}"
                )]
                for group in search_result["matches"][:10]
            ]
            await message.answer(
                f"🔍 Найдено групп {len(search_result['matches'])}:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
            )
    
    elif search_result["type"] == "room":
        if len(search_result["matches"]) == 1:
            await show_room_schedule(message, search_result["matches"][0])
        else:
            buttons = [
                [InlineKeyboardButton(
                    text=room,
                    callback_data=f"quick_room_{room}"
                )]
                for room in search_result["matches"][:10]
            ]
            await message.answer(
                f"🔍 Найдено аудиторий ({len(search_result['matches'])}:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
            )


async def show_room_schedule(message: Message, room: str):
    #Показ расписания аудитории#
    try:
        today = get_day()
        current_week = "upper" if (datetime.today().isocalendar()[1] % 2) != 0 else "lower"
        
        schedule_data = loadData("location")
        
        schedule = get_room_schedule(room, current_week, today, schedule_data)
        await message.answer(
            schedule,
            parse_mode="HTML",
            reply_markup=get_room_weekday_buttons(room)
        )
    except Exception as e:
        logging.error(f"Ошибка загрузки аудитории: {e}")
        await message.answer("Ошибка при загрузке расписания")


async def handle_room_search(message: Message):
    today = get_day()
    current_week = "upper" if (datetime.today().isocalendar()[1] % 2) != 0 else "lower"

    #Обработка поиска аудитории#
    room_input = message.text.strip()
    room = normalize_room_name(room_input)
    
    try:
        schedule_data = loadData("location")
        
        if room not in schedule_data:
            # Попробуем найти похожие аудитории
            similar_rooms = [r for r in schedule_data.keys() if room in r or room.replace("-", "") in r.replace("-", "")]
            
            if not similar_rooms:
                await message.answer("Аудитория не найдена. Попробуйте ввести номер еще раз.")
                return
            
            if len(similar_rooms) == 1:
                room = similar_rooms[0]
            else:
                # Предложим выбор из похожих аудиторий
                buttons = []
                for r in similar_rooms[:5]:  # Ограничим количество вариантов
                    buttons.append([InlineKeyboardButton(
                        text=r,
                        callback_data=f"quick_room_{r}"
                    )])
                
                await message.answer(
                    "Уточните аудиторию:",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
                )
                return
        
        schedule = get_room_schedule(room, current_week, today, schedule_data)
        await message.answer(schedule, parse_mode="HTML", reply_markup=get_room_weekday_buttons(room))
        
    except Exception as e:
        logging.error(f"Ошибка при поиске аудитории: {e}")
        await message.answer("Произошла ошибка при поиске аудитории. Попробуйте позже.")



async def handle_group_search(message: Message):
    #Обработка поиска группы#
    user_input = message.text.strip()
    group = normalize_group_name(user_input)
    
    try:
        schedule_data = loadData("schedule")
        
        # Проверяем точное совпадение
        if group in schedule_data:
            await show_group_schedule(message, group, "all")
            return
        
        # Ищем похожие группы
        similar_groups = find_group_matches(group)
        
        if not similar_groups:
            await message.answer("Группа не найдена. Попробуйте ввести полное название.")
            return
        
        if len(similar_groups) == 1:
            await show_group_schedule(message, similar_groups[0], "all")
        else:
            # Предлагаем выбрать из вариантов
            buttons = []
            for g in similar_groups[:5]:  # Ограничиваем количество вариантов
                buttons.append([InlineKeyboardButton(
                    text=g,
                    callback_data=f"quick_group_{g}"
                )])
            
            await message.answer(
                "Уточните группу:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
                
    except Exception as e:
        logging.error(f"Ошибка при поиске группы: {e}")
        await message.answer("Произошла ошибка при поиске группы. Попробуйте позже.")



async def handle_teacher_search(message: Message):
    """Обработчик поиска преподавателя с промежуточным сообщением"""
    last_name = message.text.strip()
    if not last_name.isalpha():
        await message.answer("Пожалуйста, введите только фамилию преподавателя (только буквы)")
        return
    
    teachers = find_teachers_by_last_name(last_name)
    
    if not teachers:
        await message.answer(f"Преподаватели с фамилией '{last_name}' не найдены")
        return
    
    # Формируем сообщение с кнопкой выбора
    response = "Результаты поиска\n\n"
    buttons = []
    
    for teacher in teachers[:5]:  # Ограничиваем количество вариантов
        # Разделяем ФИО для красивого отображения
        last, initials = teacher.split(" ", 1)
        response += f"▪️ {last} {initials}\n"
        buttons.append([InlineKeyboardButton(
            text=f"{last} {initials}",
            callback_data=f"teacher_select_{teacher}"
        )])
    
    # Сначала отправляем текстовое сообщение с результатами
    await message.answer(response)
    
    # Затем отправляем клавиатуру с кнопками выбора
    await message.answer(
        "Выберите преподавателя:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )



@router.callback_query(F.data.startswith("quick_room_"))
async def handle_quick_room_select(call: types.CallbackQuery):
    today = get_day()
    current_week = "upper" if (datetime.today().isocalendar()[1] % 2) != 0 else "lower"

    #Обработка быстрого выбора аудитории#
    if call.data == "quick_room_cancel":
        await call.message.delete()
        return
    
    room = call.data.split("_")[2]
    
    try:
        schedule_data = loadData("location")
        
        schedule = get_room_schedule(room, current_week, today, schedule_data)
        await call.message.edit_text(
            text=schedule,
            reply_markup=get_room_weekday_buttons(room),
            parse_mode="HTML"
        )
    except Exception as e:
        await call.answer("Произошла ошибка. Попробуйте еще раз.")



@router.callback_query(F.data.startswith("quick_group_"))
async def handle_quick_group_select(call: types.CallbackQuery):
    #Обработка выбора группы из предложенных вариантов#
    if call.data == "quick_group_cancel":
        await call.message.delete()
        return
    
    group = call.data.split("_")[2]
    await show_group_schedule(call, group, "all")



@router.callback_query(F.data.startswith("roomday_"))
async def handle_room_day_selection(call: CallbackQuery):
    try:
        _, day_type, week_type, room = call.data.split("_", 3)
        day_russian = {
            "monday": "Понедельник", "tuesday": "Вторник", "wednesday": "Среда",
            "thursday": "Четверг", "friday": "Пятница", "saturday": "Суббота"
        }.get(day_type.lower(), "Неизвестный день")
        
        schedule_data = loadData("location")
        
        schedule = get_room_schedule(room, week_type, day_russian, schedule_data)
        
        await call.message.edit_text(
            text=schedule,
            reply_markup=get_room_weekday_buttons(room),
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Ошибка при изменении дня: {e}")
        await call.answer("Произошла ошибка при загрузке расписания")


@router.callback_query(F.data == "room_schedule_back")
async def handle_room_back(call: CallbackQuery):
    #Возврат к выбору типа расписания#
    await call.message.edit_text(
        "Выберите тип расписания:",
        reply_markup=get_full_schedule_menu()
    )


@router.callback_query(F.data == "room_schedule_back")
async def handle_room_schedule_back(call: CallbackQuery):
    #Возврат к выбору типа расписания#
    await call.message.edit_text(
        "Выберите тип расписания:",
        reply_markup=get_full_schedule_menu()
    )



@router.callback_query(F.data == "full_back")
async def handle_full_back(call: CallbackQuery):
    await call.message.edit_text(
        "Выберите тип расписания:",
        reply_markup=get_full_schedule_menu()
    )








# Вспомогательные функции
def normalize_group_name(group: str) -> str:
    #Приводит название группы к стандартному формату (БИВТ-21-1)#
    group = group.upper().replace(" ", "-")
    parts = group.split("-")
    if len(parts) >= 2:
        return f"{parts[0]}-{parts[1]}" + (f"-{parts[2]}" if len(parts) > 2 else "")
    return group



def find_group_matches(query: str) -> list:
    #Находит группы, соответствующие запросу#
    groups_data = loadData("groups")
    
    query = normalize_group_name(query)
    all_groups = []
    
    # Собираем все группы из файла
    for institute in groups_data.values():
        for year_groups in institute.values():
            all_groups.extend(year_groups)
    
    # Ищем точные совпадения
    exact_matches = [g for g in all_groups if g == query]
    if exact_matches:
        return exact_matches
    
    # Ищем частичные совпадения (без номера подгруппы)
    partial_matches = [g for g in all_groups if g.startswith(query)]
    if partial_matches:
        return partial_matches
    
    # Ищем совпадения по начальным буквам и году
    if "-" in query:
        base, year = query.split("-")[:2]
        similar = [g for g in all_groups if g.startswith(base) and year in g]
        return similar
    
    return []



def normalize_room_name(room: str) -> str:
    #Нормализует формат аудитории (Л711 → Л-711)#
    room = re.sub(r'[^\w]', '', room).upper()
    if re.match(r'^[А-ЯA-Z]+\d+$', room):
        room = re.sub(r'([А-ЯA-Z]+)(\d+)', r'\1-\2', room)
    return room



def find_room_in_schedule(user_input: str, schedule: dict) -> str:
    #Находит точное название аудитории по пользовательскому вводу#
    normalized = normalize_room_name(user_input)
    
    # Проверяем точное совпадение
    if normalized in schedule:
        return normalized
    
    # Проверяем варианты без дефиса
    room_no_dash = normalized.replace("-", "")
    for room in schedule.keys():
        if room.replace("-", "") == room_no_dash:
            return room
    
    return None



async def show_group_schedule(
    message_or_call: Union[Message, CallbackQuery], 
    group: str, 
    subgroup: str
):
    today = get_day()
    current_week = "upper" if (datetime.today().isocalendar()[1] % 2) != 0 else "lower"

    #Показывает расписание для указанной группы#
    if isinstance(message_or_call, CallbackQuery):
        message = message_or_call.message
        user_id = message_or_call.from_user.id
    else:
        message = message_or_call
        user_id = message.from_user.id

    schedule_data = loadData("schedule")
    
    schedule = get_schedule(group, subgroup, current_week, today, schedule_data)
    
    # Сохраняем выбранную группу
    user_selections[user_id] = {
        "selected_group": {
            "group": group,
            "subgroup": subgroup,
            "institute": "неизвестно"
        }
    }
    
    await message.answer(
        schedule,
        reply_markup=get_weekday_buttons(),
        parse_mode="HTML"
    )






def find_teachers_by_last_name(last_name: str) -> List[str]:
    #Находит всех преподавателей по фамилии#
    try:
        teachers_data = loadData("teacher")
        
        # Ищем преподавателей, у которых фамилия начинается с запроса
        matches = []
        for full_name in teachers_data.keys():
            teacher_last_name = full_name.split()[0]  # Берем только фамилию
            if teacher_last_name.lower().startswith(last_name.lower()):
                matches.append(full_name)
        
        return sorted(matches)  # Сортируем по алфавиту
    
    except Exception as e:
        logging.error(f"Ошибка поиска преподавателей: {e}")
        return []


async def show_teacher_schedule(message: Message, teacher_name: str):
    """Показывает расписание с кнопками выбора дня и недели"""
    try:
        teachers_data = loadData("teacher")
        
        if teacher_name not in teachers_data:
            await message.answer("Расписание преподавателя не найдено")
            return
        
        # Определяем текущий день и неделю
        today = get_day()
        current_week = "upper" if (datetime.today().isocalendar()[1] % 2) != 0 else "lower"
        
        if today in teachers_data[teacher_name]:
            schedule = format_teacher_day_schedule(
                teacher_name,
                teachers_data[teacher_name][today],
                current_week,
                today  # Передаем название дня
            )
            await message.answer(
                schedule,
                parse_mode="HTML",
                reply_markup=get_teacher_weekday_buttons(teacher_name)
            )
        else:
            # Форматируем сообщение для дня без пар
            response = f"<b>Расписание {teacher_name}</b>\n\n"
            response += f"{today}, {'верхняя' if current_week == 'upper' else 'нижняя'} неделя\n\n"
            response += "Пар нет\n\n"
            response += f"Сегодня {today}, {'верхняя' if current_week == 'upper' else 'нижняя'} неделя"
            
            await message.answer(
                response,
                parse_mode="HTML",
                reply_markup=get_teacher_weekday_buttons(teacher_name)
            )
    
    except Exception as e:
        logging.error(f"Ошибка загрузки расписания: {e}")
        await message.answer("Произошла ошибка при загрузке расписания")


@router.callback_query(F.data.startswith("teacherday_"))
async def handle_teacher_day_selection(call: CallbackQuery):
    """Обработчик выбора дня и недели для преподавателя"""
    try:
        _, day_type, week_type, teacher_name = call.data.split("_", 3)
        day_russian = {
            "monday": "Понедельник", "tuesday": "Вторник",
            "wednesday": "Среда", "thursday": "Четверг",
            "friday": "Пятница", "saturday": "Суббота"
        }.get(day_type.lower(), "Понедельник")
        
        teachers_data = loadData("teacher")
        
        if teacher_name not in teachers_data or day_russian not in teachers_data[teacher_name]:
            # Форматируем сообщение для дня без расписания
            response = f"<b>Расписание {teacher_name}</b>\n\n"
            response += f"{day_russian}, {'верхняя' if week_type == 'upper' else 'нижняя'} неделя\n\n"
            response += "Пар нет\n\n"
            
            today = get_day()
            current_week = "upper" if (datetime.today().isocalendar()[1] % 2) != 0 else "lower"
            response += f"Сегодня {today}, {'верхняя' if current_week == 'upper' else 'нижняя'} неделя"
            
            await call.message.edit_text(
                text=response,
                reply_markup=get_teacher_weekday_buttons(teacher_name),
                parse_mode="HTML"
            )
            return
        
        schedule = format_teacher_day_schedule(
            teacher_name,
            teachers_data[teacher_name][day_russian],
            week_type,
            day_russian  # Передаем название дня
        )
        
        await call.message.edit_text(
            text=schedule,
            reply_markup=get_teacher_weekday_buttons(teacher_name),
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Ошибка при загрузке дня: {e}")
        await call.answer("Произошла ошибка")


def format_teacher_day_schedule(teacher_name: str, day_data: dict, week_type: str, day_name: str) -> str:
    """Форматирует расписание на один день с указанием дня"""
    response = f"<b>Расписание {teacher_name}</b>\n\n"
    response += f"{day_name}, {'верхняя' if week_type == 'upper' else 'нижняя'} неделя\n\n"
    
    times = {
        "1": "09:00 — 10:35", "2": "10:50 — 12:25", 
        "3": "12:40 — 14:15", "4": "14:30 — 16:05",
        "5": "16:20 — 17:55", "6": "18:00 — 19:25", 
        "7": "19:35 — 21:00"
    }
    
    # Проверяем наличие пар для выбранной недели
    has_pairs = any(week_type in pair_data for pair_data in day_data.values())
    
    if not has_pairs:
        response += "Пар нет\n\n"
    else:
        # Собираем все пары для выбранной недели
        pairs_info = []
        for pair_num, pair_data in sorted(day_data.items()):
            if week_type in pair_data:
                subjects = pair_data[week_type].get("subjects", {})
                
                for subject, details in subjects.items():
                    subject_name = subject.split("\n")[0]
                    locations = ", ".join(details.get("locations", []))
                    
                    # Группируем группы и подгруппы
                    groups_list = []
                    for group, group_data in details.get("groups", {}).items():
                        subgroups = group_data.get("subGroups", [])
                        if len(subgroups) == 1 and subgroups[0] == "1":
                            groups_list.append(group)
                        else:
                            groups_list.append(f"{group} [{', '.join(subgroups)}]")
                    
                    groups_text = ", ".join(groups_list)
                    
                    pairs_info.append((
                        pair_num,
                        subject_name,
                        groups_text,
                        locations
                    ))
        
        # Формируем вывод пар
        for pair_num, subject, groups, locations in pairs_info:
            response += (
                f"{pair_num} пара ({times[pair_num]})\n"
                f"<i>{subject}</i>\n"
                f"{groups}\n"
                f"{locations}\n\n"
            )
    
    # Добавляем информацию о текущем дне и неделе
    today = get_day()
    current_week = "upper" if (datetime.today().isocalendar()[1] % 2) != 0 else "lower"
    response += f"Сегодня {today}, {'верхняя' if current_week == 'upper' else 'нижняя'} неделя"
    
    return response


@router.callback_query(F.data.startswith("teacher_select_"))
async def handle_teacher_selection(call: CallbackQuery):
    """Обработчик выбора преподавателя из списка"""
    try:
        teacher_name = call.data.split("_", 2)[2]
        await call.message.delete()  # Удаляем сообщение с кнопками
        await show_teacher_schedule(call.message, teacher_name)
        await call.answer()
    except Exception as e:
        logging.error(f"Ошибка выбора преподавателя: {e}")
        await call.answer("Произошла ошибка")