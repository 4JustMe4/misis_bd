from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from typing import Union
import json
import random
import re

from handlers.keyboards import (
    get_main_menu,
    get_class_schedule_menu,
    get_institutes_menu,
    get_years_menu,
    get_groups_menu,
    get_subgroups_menu,
    get_save_confirmation_menu,
    get_weekday_buttons
)






router = Router()

# --- Временные данные профиля ---
# В реальном проекте профиль пользователя будет браться из БД
user_profile = {
    "group": "БПМ-21-1",
    "subgroup": "all",
    "saved_groups": []  # Добавляем поле для сохраненных групп
}

# Глобальные переменные для хранения выбора пользователя
user_selections = {}

def get_day():
    day = datetime.today().strftime("%A")
    days = {
        "Monday": "Понедельник",
        "Tuesday": "Вторник",
        "Wednesday": "Среда",
        "Thursday": "Четверг",
        "Friday": "Пятница",
        "Saturday": "Суббота",
        "Sunday": "Воскресенье"
    }
    return days.get(day, "Неизвестный день")

today = get_day()
current_week = "upper" if (datetime.today().isocalendar()[1] % 2) != 0 else "lower"


def add_invisible_chars(text):
    """
    Добавляет случайное количество невидимых символов (zero-width space) в текст.
    """
    invisible_char = "\u200B"  # Невидимый символ
    parts = text.split("\n")
    modified_parts = [line + invisible_char * random.randint(0, 2) for line in parts]
    return "\n".join(modified_parts)


def extract_group_from_message(text: str) -> tuple:
    """Извлекает информацию о группе из текста сообщения"""
    import re
    invisible_separator = "\u2063"
    pattern = re.compile(f"{invisible_separator}(.*?){invisible_separator}(.*?){invisible_separator}")
    match = pattern.search(text)
    if match:
        return match.group(1), match.group(2)  # group, subgroup
    return None, None







# --- Функция для получения расписания ---
def get_schedule(group, subgroup, week_type, day, schedule):
    """Получает расписание для указанной группы, подгруппы (или всех подгрупп), недели (upper/lower) и дня."""
    if group not in schedule:
        return "Расписание не найдено 🤔\n"
    
    # Если выбрана конкретная подгруппа, но её нет в расписании - показываем все подгруппы
    if subgroup != "all" and subgroup not in schedule[group]:
        subgroup = "all"
    
    response = f"<b>Расписание {group}</b>\n"
    response += f"{day}, {'верхняя' if week_type == 'upper' else 'нижняя'} неделя:\n\n"

    times = {
        "1": "9:00 — 10:35",
        "2": "10:50 — 12:25",
        "3": "12:40 — 14:15",
        "4": "14:30 — 16:05",
        "5": "16:20 — 17:55",
        "6": "18:00 — 19:25",
        "7": "19:35 — 21:00"
    }

    if subgroup == "all":
        pairs = {}
        for sub in schedule[group]:
            if day not in schedule[group][sub]:
                continue

            for pair_num, pair_data in schedule[group][sub][day].items():
                week_data = pair_data.get(week_type, {"subject": "", "place": ""})
                
                if not week_data["subject"] and not week_data["place"]:
                    continue

                key = (pair_num, week_data["subject"], week_data["place"])
                if key not in pairs:
                    pairs[key] = set()
                pairs[key].add(sub)

        if pairs:
            for (pair_num, subject, place), subgroups in sorted(pairs.items()):
                response += (
                    f"{pair_num} пара ({times.get(pair_num, 'неизвестное время')})\n"
                    f"<b>{subject}</b>\n"
                    f"{group} [{', '.join(subgroups)}]\n"
                    f"{place}\n\n"
                )
        else:
            response += "На этот день занятий нет 🥳\n"
    else:
        if day not in schedule[group][subgroup]:
            return "На этот день занятий нет 🥳\n"

        pairs = []
        for pair_num, pair_data in schedule[group][subgroup][day].items():
            week_data = pair_data.get(week_type, {"subject": "", "place": ""})
            
            if not week_data["subject"] and not week_data["place"]:
                continue

            pairs.append({
                "num": pair_num,
                "time": times.get(pair_num, "неизвестное время"),
                "subject": week_data["subject"],
                "place": week_data["place"]
            })

        if pairs:
            for pair in pairs:
                response += (
                    f"{pair['num']} пара ({pair['time']})\n"
                    f"<b>{pair['subject']}</b>\n"
                    f"{pair['place']}\n\n"
                )
        else:
            response += "На этот день занятий нет 🥳\n"

    response += f"Сегодня {today}, {'верхняя' if week_type == 'upper' else 'нижняя'} неделя\n"
    # Добавляем метаданные в виде невидимых символов
    invisible_separator = "\u2063"  # Невидимый разделитель
    metadata = f"{invisible_separator}{group}{invisible_separator}{subgroup}{invisible_separator}"
    return add_invisible_chars(response + metadata)







# --- Хэндлер "Расписание занятий" ---
@router.message(F.text == "Сегодня")
async def today_schedule(message: Message):
    """Вывод расписания на текущий день."""
    if "group" not in user_profile:
        await message.answer("Вы не зарегистрированы. Заполните данные в /my_profile")
        return
    
    group = user_profile["group"]
    subgroup = user_profile["subgroup"]

    with open("data/schedule.json", "r", encoding="utf-8") as file:
        schedule = json.load(file)

    response = get_schedule(group, subgroup, current_week, today, schedule)

    await message.answer(response, parse_mode='HTML')








# --- Хэндлер "Мое расписание" ---
@router.message(F.text == "Мое расписание")
async def my_schedule(message: Message):
    """Отображение расписания для группы пользователя с плавающими кнопками."""
    if "group" not in user_profile:
        await message.answer("Вы не зарегистрированы. Заполните данные в /my_profile")
        return

    group = user_profile["group"]
    subgroup = user_profile["subgroup"]

    with open("data/schedule.json", "r", encoding="utf-8") as file:
        schedule = json.load(file)

    response = get_schedule(group, subgroup, current_week, today, schedule)

    await message.answer(response, reply_markup=get_weekday_buttons(), parse_mode='HTML')


# --- Хэндлер выбора дня в "Мое расписание" ---
@router.callback_query(F.data.startswith("weekday_"))
async def weekday_callback(call: types.CallbackQuery):
    """Обработка выбора дня недели"""
    try:
        # Извлекаем группу из текущего сообщения
        group, subgroup = extract_group_from_message(call.message.text or "")
        
        # Если не нашли в сообщении, используем последний выбор
        if not group:
            if call.from_user.id in user_selections and "selected_group" in user_selections[call.from_user.id]:
                group = user_selections[call.from_user.id]["selected_group"]["group"]
                subgroup = user_selections[call.from_user.id]["selected_group"]["subgroup"]
            else:
                group = user_profile.get("group", "БПМ-21-1")
                subgroup = user_profile.get("subgroup", "all")

        # Остальная логика без изменений
        parts = call.data.split("_")
        day_part, week = parts[1], parts[2]
        day = day_part.capitalize()
        
        days = {
            "Monday": "Понедельник",
            "Tuesday": "Вторник",
            "Wednesday": "Среда",
            "Thursday": "Четверг",
            "Friday": "Пятница",
            "Saturday": "Суббота"
        }
        day = days.get(day, "Неизвестный день")

        with open("data/schedule.json", "r", encoding="utf-8") as file:
            schedule = json.load(file)

        response = get_schedule(group, subgroup, week, day, schedule)
        await call.message.edit_text(
            text=response,
            reply_markup=get_weekday_buttons(),
            parse_mode='HTML'
        )
    except Exception as e:
        await call.answer(f"Ошибка: {str(e)}")



async def update_or_send_message(bot: Bot, message: Message, new_text: str, reply_markup=None, parse_mode=None):
    """Обновляет существующее сообщение или отправляет новое."""
    try:
        if message.from_user.id in user_selections and "message_id" in user_selections[message.from_user.id]:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=user_selections[message.from_user.id]["message_id"],
                text=new_text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        else:
            msg = await message.answer(new_text, reply_markup=reply_markup, parse_mode=parse_mode)
            user_selections[message.from_user.id]["message_id"] = msg.message_id
    except Exception as e:
        print(f"Ошибка при обновлении сообщения: {e}")
        msg = await message.answer(new_text, reply_markup=reply_markup, parse_mode=parse_mode)
        user_selections[message.from_user.id]["message_id"] = msg.message_id










# Обработчик начала выбора
@router.message(F.text == "Поиск расписания")
async def full_schedule_start(message: Message):
    """Начало выбора полного расписания"""
    user_selections[message.from_user.id] = {}
    await message.answer(
        "Выберите институт:",
        reply_markup=get_institutes_menu()
    )

# Обработчики callback-запросов
@router.callback_query(F.data.startswith("inst_"))
async def choose_institute(call: types.CallbackQuery):
    """Обработка выбора института"""
    institute = call.data.split("_")[1]
    user_selections[call.from_user.id] = {"institute": institute}
    
    await call.message.edit_text(
        f"Выберите курс обучения в институте {institute}:",
        reply_markup=get_years_menu(institute)
    )

@router.callback_query(F.data.startswith("year_"))
async def choose_year(call: types.CallbackQuery):
    """Обработка выбора курса"""
    year = call.data.split("_")[1]
    user_id = call.from_user.id
    
    if user_id not in user_selections:
        await call.answer("Пожалуйста, начните выбор сначала.")
        return
    
    user_selections[user_id]["year"] = year
    institute = user_selections[user_id]["institute"]
    
    await call.message.edit_text(
        f"Выберите академическую группу в институте {institute}, курс {year}:",
        reply_markup=get_groups_menu(institute, year)
    )

@router.callback_query(F.data.startswith("group_"))
async def choose_group(call: types.CallbackQuery):
    """Обработка выбора группы"""
    group = call.data.split("_")[1]
    user_id = call.from_user.id
    
    if user_id not in user_selections or "year" not in user_selections[user_id]:
        await call.answer("Пожалуйста, начните выбор сначала.")
        return
    
    user_selections[user_id]["group"] = group
    institute = user_selections[user_id]["institute"]
    
    await call.message.edit_text(
        f"Выберите подгруппу для группы {group}, {institute}:",
        reply_markup=get_subgroups_menu()
    )

@router.callback_query(F.data.startswith("subgroup_"))
async def choose_subgroup(call: types.CallbackQuery):
    """Обработка выбора подгруппы"""
    subgroup = call.data.split("_")[1]
    user_id = call.from_user.id
    
    if user_id not in user_selections or "group" not in user_selections[user_id]:
        await call.answer("Пожалуйста, начните выбор сначала.")
        return
    
    subgroup = subgroup if subgroup != "all" else "all"
    user_selections[user_id]["subgroup"] = subgroup
    group = user_selections[user_id]["group"]
    institute = user_selections[user_id]["institute"]
    
    user_selections[user_id]["selected_group"] = {
        "group": group,
        "subgroup": subgroup,
        "institute": institute
    }
    
    await call.message.edit_text(
        f"Сохранить группу {group}({subgroup}) в избранное?",
        reply_markup=get_save_confirmation_menu()
    )



@router.callback_query(F.data.startswith("save_"))
async def confirm_save(call: types.CallbackQuery):
    """Обработка подтверждения сохранения"""
    try:
        action = call.data.split("_")[1]
        user_id = call.from_user.id
        
        if user_id not in user_selections or "selected_group" not in user_selections[user_id]:
            await call.answer("Пожалуйста, начните выбор сначала.")
            return
        
        selected = user_selections[user_id]["selected_group"]
        group = selected["group"]
        subgroup = selected["subgroup"]
        
        if action == "yes":
            if "saved_groups" not in user_profile:
                user_profile["saved_groups"] = []
            
            if not any(g["group"] == group for g in user_profile["saved_groups"]):
                user_profile["saved_groups"].append(selected)
                await call.answer("Группа сохранена в избранное! ✅")

        with open("data/schedule.json", "r", encoding="utf-8") as f:
            schedule_data = json.load(f)
        
        schedule = get_schedule(group, subgroup, current_week, today, schedule_data)
        
        # Убедимся, что сообщение можно отредактировать
        try:
            await call.message.edit_text(
                text=schedule,
                reply_markup=get_weekday_buttons(),
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Ошибка при редактировании сообщения: {e}")
            await call.message.answer(
                text=schedule,
                reply_markup=get_weekday_buttons(),
                parse_mode="HTML"
            )
    except Exception as e:
        print(f"Ошибка в confirm_save: {e}")
        await call.answer("Произошла ошибка, попробуйте ещё раз")
    
    # Очищаем выбор пользователя
    #user_selections.pop(user_id, None)



# Обработчики кнопок "Назад"
@router.callback_query(F.data == "back_to_main")
async def back_to_main(call: types.CallbackQuery):
    """Возврат в главное меню"""
    await call.message.edit_text(
        "Выберите действие:",
        reply_markup=get_class_schedule_menu()
    )



@router.callback_query(F.data == "back_to_inst")
async def back_to_institutes(call: types.CallbackQuery):
    """Возврат к выбору института"""
    await call.message.edit_text(
        "Выберите институт:",
        reply_markup=get_institutes_menu()
    )



@router.callback_query(F.data.startswith("back_to_years_"))
async def back_to_years(call: types.CallbackQuery):
    """Возврат к выбору курса"""
    institute = call.data.split("_")[-1]
    await call.message.edit_text(
        f"Выберите курс обучения в институте {institute}:",
        reply_markup=get_years_menu(institute)
    )



@router.callback_query(F.data == "back_to_groups")
async def back_to_groups(call: types.CallbackQuery):
    """Возврат к выбору группы"""
    user_id = call.from_user.id
    if user_id not in user_selections:
        await call.answer("Пожалуйста, начните выбор сначала.")
        return
    
    institute = user_selections[user_id]["institute"]
    year = user_selections[user_id]["year"]
    
    await call.message.edit_text(
        f"Выберите академическую группу в институте {institute}, курс {year}:",
        reply_markup=get_groups_menu(institute, year)
    )



@router.callback_query(F.data == "back_to_subgroups")
async def back_to_subgroups(call: types.CallbackQuery):
    """Возврат к выбору подгруппы"""
    user_id = call.from_user.id
    if user_id not in user_selections or "group" not in user_selections[user_id]:
        await call.answer("Пожалуйста, начните выбор сначала.")
        return
    
    group = user_selections[user_id]["group"]
    institute = user_selections[user_id]["institute"]
    
    await call.message.edit_text(
        f"Выберите подгруппу для группы {group}, {institute}:",
        reply_markup=get_subgroups_menu()
    )









def normalize_group_name(group: str) -> str:
    """Приводит название группы к стандартному формату (БИВТ-21-1)"""
    group = group.upper().replace(" ", "-")
    parts = group.split("-")
    if len(parts) >= 2:
        return f"{parts[0]}-{parts[1]}" + (f"-{parts[2]}" if len(parts) > 2 else "")
    return group

def find_group_matches(query: str) -> list:
    """Находит группы, соответствующие запросу"""
    with open("data/groups.json", "r", encoding="utf-8") as f:
        groups_data = json.load(f)
    
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



async def show_group_schedule(
    message_or_call: Union[Message, CallbackQuery], 
    group: str, 
    subgroup: str
):
    """Показывает расписание для указанной группы"""
    if isinstance(message_or_call, CallbackQuery):
        message = message_or_call.message
        user_id = message_or_call.from_user.id
    else:
        message = message_or_call
        user_id = message.from_user.id

    with open("data/schedule.json", "r", encoding="utf-8") as f:
        schedule_data = json.load(f)
    
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



@router.message(F.text)
async def handle_direct_group_input(message: Message):
    """Обработка прямого ввода группы пользователем"""
    user_input = message.text.strip()
    
    # Проверяем, похоже ли на формат группы
    if not re.match(r"^[А-ЯЁ]{2,}", user_input):
        return
    
    with open("data/schedule.json", "r", encoding="utf-8") as f:
        schedule_data = json.load(f)
    
    # Проверяем точное совпадение
    if user_input in schedule_data:
        await show_group_schedule(message, user_input, "all")
        return
    
    # Ищем похожие группы
    similar_groups = find_group_matches(user_input)
    
    if not similar_groups:
        await message.answer("Группа не найдена. Попробуйте ввести полное название.")
        return
    
    if len(similar_groups) == 1:
        # Если нашли только один вариант - показываем сразу
        await show_group_schedule(message, similar_groups[0], "all")
    else:
        # Предлагаем выбрать из вариантов
        buttons = []
        for group in similar_groups[:10]:  # Ограничиваем количество вариантов
            buttons.append([InlineKeyboardButton(
                text=group,
                callback_data=f"quick_group_{group}"
            )])
        
        buttons.append([InlineKeyboardButton(
            text="Отмена",
            callback_data="quick_group_cancel"
        )])
        
        await message.answer(
            "Уточните группу:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data.startswith("quick_group_"))
async def handle_quick_group_select(call: types.CallbackQuery):
    """Обработка выбора группы из предложенных вариантов"""
    if call.data == "quick_group_cancel":
        await call.message.delete()
        return
    
    group = call.data.split("_")[2]
    await show_group_schedule(call, group, "all")
