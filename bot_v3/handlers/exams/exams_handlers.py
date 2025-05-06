import json
import os
from typing import Dict, List, Optional

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from handlers.loader import loadData

# Создаем роутер
router = Router()

# Состояния для FSM
class SessionStates(StatesGroup):
    waiting_for_institute = State()
    waiting_for_year = State()
    waiting_for_group = State()

# --- Вспомогательные функции ---
def load_users_data() -> Dict:
    """Загружает данные пользователей"""
    return loadData("users")

def load_session_data() -> Dict:
    """Загружает данные сессии"""
    return loadData("session")

def load_groups_data() -> Dict:
    """Загружает данные групп"""
    return loadData("groups")

def get_user_main_group(user_id: str) -> Optional[str]:
    """Получает основную группу пользователя"""
    users = load_users_data()
    return users.get(str(user_id), {}).get("main_group")

def format_exam_day(date: str, exams: Dict) -> str:
    """Форматирует день с экзаменами в читаемый текст"""
    parts = []
    
    for part_num, exam_data in exams.items():
        if exam_data.get("subject"):
            time = "9:00-12:00" if part_num == "1" else "13:00-16:00"
            parts.append(
                f"▪️ {time} - <b>{exam_data['subject']}</b>\n"
                f"📍 {exam_data['place'] or 'Аудитория не указана'}"
            )
    
    if not parts:
        return ""
    
    return f"📅 <b>{date}</b>\n" + "\n\n".join(parts) + "\n"

def get_session_schedule(group_name: str, session_path: str = "data/session.json") -> str:
    data = loadData("session")
    
    if group_name not in data:
        return f"❌ Расписание сессии для группы {group_name} не найдено."

    result_lines = [f"📝 Экзамены для вашей группы {group_name}:"]
    subgroup_data = data[group_name]

    for subgroup, dates in subgroup_data.items():
        for date, halves in dates.items():
            for half_day, session in halves.items():
                subject = session.get('subject', '').strip()
                place = session.get('place', '').strip()

                if subject:
                    half_str = "первая половина дня" if half_day == "1" else "вторая половина дня"
                    place_str = place if place else "аудитория не указана"
                    result_lines.append(
                        f"👾 {subject} {date}, {half_str} {place_str}"
                    )

    if len(result_lines) == 1:
        return f"ℹ️ Для группы {group_name} пока нет информации о сессии."
    
    return "\n".join(result_lines)

# --- Клавиатуры ---
def get_session_menu() -> ReplyKeyboardMarkup:
    """Клавиатура меню сессии"""
    buttons = [
        [KeyboardButton(text="Мои экзамены")],
        [KeyboardButton(text="Экзамены по группам")],
        [KeyboardButton(text="Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_institutes_menu() -> InlineKeyboardMarkup:
    """Клавиатура с выбором института (Inline)"""
    groups_data = load_groups_data()
    institutes = list(groups_data.keys())
    buttons = []
    
    # Разбиваем на ряды по 3 кнопки
    for i in range(0, len(institutes), 3):
        row = institutes[i:i+3]
        buttons.append([InlineKeyboardButton(text=inst, callback_data=f"exams_inst_{inst}") for inst in row])
    
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="exams_back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_years_menu(institute: str) -> InlineKeyboardMarkup:
    """Клавиатура с выбором курса (Inline)"""
    groups_data = load_groups_data()
    years = list(groups_data.get(institute, {}).keys())
    buttons = []
    
    # Разбиваем на ряды по 2 кнопки
    for i in range(0, len(years), 2):
        row = years[i:i+2]
        buttons.append([InlineKeyboardButton(text=year, callback_data=f"exams_year_{year}") for year in row])
    
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="exams_back_to_inst")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_groups_menu(institute: str, year: str) -> InlineKeyboardMarkup:
    """Клавиатура с выбором группы (Inline)"""
    groups_data = load_groups_data()
    groups = groups_data.get(institute, {}).get(year, [])
    buttons = []
    
    # Разбиваем на ряды по 3 кнопки
    for i in range(0, len(groups), 3):
        row = groups[i:i+3]
        buttons.append([InlineKeyboardButton(text=group, callback_data=f"exams_group_{group}") for group in row])
    
    buttons.append([InlineKeyboardButton(text="Назад", callback_data=f"exams_back_to_years_{institute}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- Обработчики сообщений ---
@router.message(F.text == "Расписание сессии")
@router.message(F.text == "Назад в меню сессии")
async def show_session_menu(message: Message):
    """Показывает меню сессии"""
    await message.answer(
        "Выберите действие:",
        reply_markup=get_session_menu()
    )

@router.message(F.text == "Мои экзамены")
async def show_my_exams(message: Message):
    """Показывает экзамены для основной группы пользователя"""
    user_id = str(message.from_user.id)
    main_group = get_user_main_group(user_id)
    
    if not main_group:
        await message.answer("❌ Основная группа не указана в вашем профиле.")
        return
    
    session_data = load_session_data()
    group_exams = session_data.get(main_group, {}).get("1", {})  # Подгруппа 1
    
    if not group_exams:
        await message.answer(f"ℹ️ Для вашей группы {main_group} нет данных об экзаменах.")
        return
    
    result = [f"📝 Экзамены для вашей группы {main_group}:\n"]
    
    for date, exams in sorted(group_exams.items()):
        formatted = format_exam_day(date, exams)
        if formatted:
            result.append(formatted)
    
    if len(result) == 1:
        await message.answer(f"ℹ️ Для вашей группы {main_group} пока нет запланированных экзаменов.")
    else:
        await message.answer("\n".join(result), parse_mode='HTML')

@router.message(F.text == "Экзамены по группам")
async def start_group_search(message: Message, state: FSMContext):
    """Начинает процесс поиска по группам"""
    await message.answer(
        "Выберите институт:",
        reply_markup=get_institutes_menu()
    )
    await state.set_state(SessionStates.waiting_for_institute)

# --- Обработчики колбэков ---
@router.callback_query(F.data.startswith("exams_inst_"))
async def process_institute_selection(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает выбор института"""
    institute = callback.data.replace("exams_inst_", "")
    await state.update_data(institute=institute)
    
    await callback.message.edit_text(
        f"Институт: {institute}\nВыберите курс:",
        reply_markup=get_years_menu(institute)
    )
    await state.set_state(SessionStates.waiting_for_year)
    await callback.answer()

@router.callback_query(F.data.startswith("exams_year_"))
async def process_year_selection(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает выбор курса"""
    year = callback.data.replace("exams_year_", "")
    data = await state.get_data()
    institute = data.get("institute")
    
    await state.update_data(year=year)
    
    await callback.message.edit_text(
        f"Институт: {institute}\nКурс: {year}\nВыберите группу:",
        reply_markup=get_groups_menu(institute, year)
    )
    await state.set_state(SessionStates.waiting_for_group)
    await callback.answer()

@router.callback_query(F.data.startswith("exams_group_"))
async def process_group_selection(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает выбор группы и показывает экзамены"""
    group = callback.data.replace("exams_group_", "")
    session_data = load_session_data()
    group_exams = session_data.get(group, {}).get("1", {})  # Подгруппа 1
    
    if not group_exams:
        await callback.message.answer(f"ℹ️ Для группы {group} нет данных об экзаменах.")
        await state.clear()
        return
    
    result = [f"📝 Экзамены для группы {group}:\n"]
    
    for date, exams in sorted(group_exams.items()):
        formatted = format_exam_day(date, exams)
        if formatted:
            result.append(formatted)
    
    if len(result) == 1:
        await callback.message.answer(f"ℹ️ Для группы {group} пока нет запланированных экзаменов.")
    else:
        await callback.message.answer("\n".join(result), parse_mode='HTML')
    
    await state.clear()
    await callback.answer()

# Навигационные колбэки
@router.callback_query(F.data == "exams_back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в меню сессии"""
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=get_session_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "exams_back_to_inst")
async def back_to_institutes(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору института"""
    await callback.message.edit_text(
        "Выберите институт:",
        reply_markup=get_institutes_menu()
    )
    await state.set_state(SessionStates.waiting_for_institute)
    await callback.answer()

@router.callback_query(F.data.startswith("exams_back_to_years_"))
async def back_to_years(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору курса"""
    institute = callback.data.replace("exams_back_to_years_", "")
    await state.update_data(institute=institute)
    
    await callback.message.edit_text(
        f"Институт: {institute}\nВыберите курс:",
        reply_markup=get_years_menu(institute)
    )
    await state.set_state(SessionStates.waiting_for_year)
    await callback.answer()

@router.message(F.text == "Назад в главное меню")
async def back_to_main_menu(message: Message, state: FSMContext):
    """Возврат в главное меню"""
    from handlers.user_profile import get_main_menu
    await state.clear()
    await message.answer(
        "Главное меню:",
        reply_markup=get_main_menu()
    )