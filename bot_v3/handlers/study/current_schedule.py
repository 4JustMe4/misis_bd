import logging
from aiogram import Router, F, types
from aiogram.types import Message

import json
import random
from datetime import datetime, timedelta

from handlers.loader import loadData
from handlers.user_profile.profile_keyboards import get_profile_keyboard
from handlers.user_profile.profile_utils import load_user_profile

from .common import get_user_profile, user_selections, get_day, get_tomorrow

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
    user_id = message.from_user.id
    user_profile = load_user_profile(message.from_user.id)

    #Вывод расписания на текущий день.#
    if not user_profile.get("main_group"):
            await message.answer(
                "❌ Основная группа не выбрана!\n"
                "Используйте /profile для настройки",
                reply_markup=get_profile_keyboard()  # Даем быстрый доступ
            )
            return
    
    group = user_profile["main_group"]
    subgroup = user_profile["subgroup"]

    schedule = loadData("schedule")

    response = get_schedule_new(user_id, group, subgroup, current_week, today, schedule)

    await message.answer(response, parse_mode='HTML')


@router.message(F.text == "Завтра")
async def today_schedule(message: Message):
    tomorrow = get_tomorrow()
    current_week = "upper" if ((datetime.today()+timedelta(days=1)).isocalendar()[1] % 2) != 0 else "lower"
    user_id = message.from_user.id
    user_profile = load_user_profile(message.from_user.id)

    #Вывод расписания на текущий день.#
    if not user_profile.get("main_group"):
            await message.answer(
                "❌ Основная группа не выбрана!\n"
                "Используйте /profile для настройки",
                reply_markup=get_profile_keyboard()  # Даем быстрый доступ
            )
            return
    
    group = user_profile["main_group"]
    subgroup = user_profile["subgroup"]

    schedule = loadData("schedule")

    response = get_schedule_next(user_id, group, subgroup, current_week, tomorrow, schedule)

    await message.answer(response, parse_mode='HTML')


# --- Хэндлер "Мое расписание" ---
@router.message(F.text == "Мое расписание")
async def my_schedule(message: Message):
    today = get_day()
    current_week = "upper" if (datetime.today().isocalendar()[1] % 2) != 0 else "lower"
    user_id = message.from_user.id
    user_profile = load_user_profile(message.from_user.id)

    #Отображение расписания для группы пользователя с плавающими кнопками.#
    if not user_profile.get("main_group"):
            await message.answer(
                "❌ Основная группа не выбрана!\n"
                "Используйте /profile для настройки",
                reply_markup=get_profile_keyboard()  # Даем быстрый доступ
            )
            return

    group = user_profile["main_group"]
    subgroup = user_profile["subgroup"]

    schedule = loadData("schedule")

    response = get_schedule_new(user_id, group, subgroup, current_week, today, schedule)

    await message.answer(response, reply_markup=get_weekday_buttons(), parse_mode='HTML')


# --- Хэндлер выбора дня в "Мое расписание" ---
@router.callback_query(F.data.startswith("weekday_"))
async def weekday_callback(call: types.CallbackQuery):
    """Обработчик выбора дня недели с сохранением группы из профиля"""
    try:
        # 1. Загружаем актуальный профиль пользователя
        profile = load_user_profile(call.from_user.id)
        user_id = call.from_user.id
        
        # 2. Определяем группу и подгруппу (в порядке приоритета):
        #    - Из метаданных сообщения
        #    - Из сохраненного выбора
        #    - Из профиля пользователя
        group, subgroup = extract_group_from_message(call.message.text or "")
        
        if not group:
            if call.from_user.id in user_selections and "selected_group" in user_selections[call.from_user.id]:
                group = user_selections[call.from_user.id]["selected_group"]["group"]
                subgroup = user_selections[call.from_user.id]["selected_group"]["subgroup"]
            else:
                group = profile.get("main_group")
                subgroup = profile.get("subgroup", "all")
                
                # Если в профиле нет группы - отправляем на настройку
                if not group:
                    await call.answer("❌ Группа не выбрана. Используйте /profile")
                    await call.message.edit_text(
                        "Пожалуйста, сначала выберите основную группу:",
                        reply_markup=get_profile_keyboard()
                    )
                    return

        # 3. Получаем выбранный день и неделю
        parts = call.data.split("_")
        day_part, week = parts[1], parts[2]
        
        days_mapping = {
            "Monday": "Понедельник",
            "Tuesday": "Вторник",
            "Wednesday": "Среда",
            "Thursday": "Четверг",
            "Friday": "Пятница",
            "Saturday": "Суббота"
        }
        day = days_mapping.get(day_part.capitalize(), "Неизвестный день")

        # 4. Загружаем расписание
        schedule = loadData("schedule")

        # 5. Формируем ответ с ЯВНЫМ указанием группы
        response = (
            f"<b>Расписание {group} {subgroup}</b>\n"
            f"{day}, {'верхняя' if week == 'upper' else 'нижняя'} неделя:\n\n"
            f"{get_schedule_new(user_id, group, subgroup, week, day, schedule)}"
        )

        # 6. Обновляем сообщение
        await call.message.edit_text(
            text=response,
            reply_markup=get_weekday_buttons(),
            parse_mode='HTML'
        )
        
        # 7. Сохраняем выбранную группу в сессии
        if call.from_user.id not in user_selections:
            user_selections[call.from_user.id] = {}
        user_selections[call.from_user.id]["selected_group"] = {
            "group": group,
            "subgroup": subgroup
        }

    except json.JSONDecodeError:
        await call.answer("❌ Ошибка загрузки расписания")
    except Exception as e:
        logging.error(f"Weekday callback error: {e}")
        await call.answer("⚠️ Ошибка при загрузке расписания")



# Вспомогательные функции
# Загружаем пользователей и группы по английскому
with open("data/users.json", encoding="utf-8") as f:
    USERS = json.load(f)

with open("data/english_groups.json", encoding="utf-8") as f:
    ENGLISH_GROUPS = json.load(f)

def get_schedule_new(user_id, group, subgroup, week_type, day, schedule):
    today = get_day()

    # Получаем данные пользователя
    user = USERS.get(str(user_id), {})
    english_group = user.get("english_group")
    user_subgroup = user.get("subgroup", subgroup)  # используем из users.json или переданное

    # Получаем кабинет английского, если данные есть
    english_room = None
    if english_group and english_group in ENGLISH_GROUPS:
        english_room = ENGLISH_GROUPS[english_group].get(week_type, {}).get(user_subgroup)

    if group not in schedule:
        return "Расписание не найдено 🤔\n"

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
                subject = week_data["subject"].rstrip()
                place = week_data["place"]

                # Подмена кабинета для английского языка
                if (
                    subject.startswith("Иностранный язык")
                    and place == "Каф. ИЯКТ"
                    and english_room
                ):
                    place = english_room

                if not subject and not place:
                    continue

                key = (pair_num, subject, place)
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
            subject = week_data["subject"]
            place = week_data["place"]

            # Подмена кабинета для английского языка
            if (
                subject.startswith("Иностранный язык")
                and place == "Каф. ИЯКТ"
                and english_room
            ):
                place = english_room

            if not subject and not place:
                continue

            pairs.append({
                "num": pair_num,
                "time": times.get(pair_num, "неизвестное время"),
                "subject": subject,
                "place": place
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
    invisible_separator = "\u2063"
    metadata = f"{invisible_separator}{group}{invisible_separator}[{subgroup}]{invisible_separator}"
    return add_invisible_chars(response + metadata)




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
    metadata = f"{invisible_separator}{group}{invisible_separator}[{subgroup}]{invisible_separator}"
    return add_invisible_chars(response + metadata)


def get_schedule_next(user_id, group, subgroup, week_type, day, schedule):
    today = get_tomorrow()

    # Получаем данные пользователя
    user = USERS.get(str(user_id), {})
    english_group = user.get("english_group")
    user_subgroup = user.get("subgroup", subgroup)

    # Получаем кабинет английского, если есть
    english_room = None
    if english_group and english_group in ENGLISH_GROUPS:
        english_room = ENGLISH_GROUPS[english_group].get(week_type, {}).get(user_subgroup)

    if group not in schedule:
        return "Расписание не найдено 🤔\n"

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
                subject = week_data["subject"]
                place = week_data["place"]

                # Подмена кабинета, если это английский
                if (
                    subject.startswith("Иностранный язык")
                    and place == "Каф. ИЯКТ"
                    and english_room
                ):
                    place = english_room

                if not subject and not place:
                    continue

                key = (pair_num, subject, place)
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
            subject = week_data["subject"].rstrip()
            place = week_data["place"]

            # Подмена кабинета для английского языка
            if (
                subject.startswith("Иностранный язык")
                and place == "Каф. ИЯКТ"
                and english_room
            ):
                place = english_room

            if not subject and not place:
                continue

            pairs.append({
                "num": pair_num,
                "time": times.get(pair_num, "неизвестное время"),
                "subject": subject,
                "place": place
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
    invisible_separator = "\u2063"
    metadata = f"{invisible_separator}{group}{invisible_separator}[{subgroup}]{invisible_separator}"
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