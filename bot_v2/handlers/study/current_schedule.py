from aiogram import Router, F, types
from aiogram.types import Message

import json
import random
from datetime import datetime, timedelta

from .common import user_profile, user_selections, get_day, get_tomorrow

from handlers.keyboards import (
    get_weekday_buttons
)

router = Router()


# Хэндлеры
# --- Хэндлер "Расписание занятий" ---
@router.message(F.text == "Сегодня")
async def today_schedule(message: Message):
    today = get_day()
    current_week = "upper" if (datetime.today().isocalendar()[1] % 2) != 0 else "lower"

    #Вывод расписания на текущий день.#
    if "group" not in user_profile:
        await message.answer("Вы не зарегистрированы. Заполните данные в /my_profile")
        return
    
    group = user_profile["group"]
    subgroup = user_profile["subgroup"]

    with open("data/schedule.json", "r", encoding="utf-8") as file:
        schedule = json.load(file)

    response = get_schedule(group, subgroup, current_week, today, schedule)

    await message.answer(response, parse_mode='HTML')


@router.message(F.text == "Завтра")
async def today_schedule(message: Message):
    tomorrow = get_tomorrow()
    current_week = "upper" if ((datetime.today()+timedelta(days=1)).isocalendar()[1] % 2) != 0 else "lower"

    #Вывод расписания на текущий день.#
    if "group" not in user_profile:
        await message.answer("Вы не зарегистрированы. Заполните данные в /my_profile")
        return
    
    group = user_profile["group"]
    subgroup = user_profile["subgroup"]

    with open("data/schedule.json", "r", encoding="utf-8") as file:
        schedule = json.load(file)

    response = get_schedule_next(group, subgroup, current_week, tomorrow, schedule)

    await message.answer(response, parse_mode='HTML')


# --- Хэндлер "Мое расписание" ---
@router.message(F.text == "Мое расписание")
async def my_schedule(message: Message):
    today = get_day()
    current_week = "upper" if (datetime.today().isocalendar()[1] % 2) != 0 else "lower"

    #Отображение расписания для группы пользователя с плавающими кнопками.#
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
    #Обработка выбора дня недели#
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



# Вспомогательные функции
# --- Функция для получения расписания ---
def get_schedule(group, subgroup, week_type, day, schedule):
    today = get_day()
    
    #Получает расписание для указанной группы, подгруппы (или всех подгрупп), недели (upper/lower) и дня.#
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


def get_schedule_next(group, subgroup, week_type, day, schedule):
    today = get_tomorrow()
    
    #Получает расписание для указанной группы, подгруппы (или всех подгрупп), недели (upper/lower) и дня.#
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

    response += f"Завтра {today}, {'верхняя' if week_type == 'upper' else 'нижняя'} неделя\n"
    # Добавляем метаданные в виде невидимых символов
    invisible_separator = "\u2063"  # Невидимый разделитель
    metadata = f"{invisible_separator}{group}{invisible_separator}{subgroup}{invisible_separator}"
    return add_invisible_chars(response + metadata)



def add_invisible_chars(text):
    #Добавляет случайное количество невидимых символов (zero-width space) в текст.#
    invisible_char = "\u200B"  # Невидимый символ
    parts = text.split("\n")
    modified_parts = [line + invisible_char * random.randint(0, 2) for line in parts]
    return "\n".join(modified_parts)


def extract_group_from_message(text: str) -> tuple:
    #Извлекает информацию о группе из текста сообщения#
    import re
    invisible_separator = "\u2063"
    pattern = re.compile(f"{invisible_separator}(.*?){invisible_separator}(.*?){invisible_separator}")
    match = pattern.search(text)
    if match:
        return match.group(1), match.group(2)  # group, subgroup
    return None, None