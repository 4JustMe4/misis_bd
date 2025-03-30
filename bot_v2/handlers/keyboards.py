from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import json

def get_main_menu() -> ReplyKeyboardMarkup:
    """Клавиатура с главным меню."""
    buttons = [
        [KeyboardButton(text="Расписание занятий")],
        [KeyboardButton(text="Расписание сессии")],
        [KeyboardButton(text="Расписание пересдач")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


# --- Главное меню расписания ---
def get_class_schedule_menu() -> ReplyKeyboardMarkup:
    """Клавиатура с основным меню расписания."""
    buttons = [
        [KeyboardButton(text="Сегодня"), KeyboardButton(text="Завтра")],
        [KeyboardButton(text="Мое расписание")],
        [KeyboardButton(text="Поиск расписания")],
        [KeyboardButton(text="Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


# --- Переход с "Поиск расписания" ---
def get_full_schedule_menu() -> InlineKeyboardMarkup:
    """Меню выбора типа расписания"""
    buttons = [
        [InlineKeyboardButton(text="По группам", callback_data="full_group")],
        [InlineKeyboardButton(text="По преподавателям", callback_data="full_teacher")],
        [InlineKeyboardButton(text="По аудиториям", callback_data="full_room")]
        #[InlineKeyboardButton(text="Назад", callback_data="full_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# --- Дни недели (upper и lower неделя) ---
def get_weekday_buttons() -> InlineKeyboardMarkup:
    """Генерация кнопок дней недели для 'Моего расписания'."""
    buttons = [
        [
            InlineKeyboardButton(text="ПН", callback_data="weekday_monday_upper"),
            InlineKeyboardButton(text="ВТ", callback_data="weekday_tuesday_upper"),
            InlineKeyboardButton(text="СР", callback_data="weekday_wednesday_upper"),
            InlineKeyboardButton(text="ЧТ", callback_data="weekday_thursday_upper"),
            InlineKeyboardButton(text="ПТ", callback_data="weekday_friday_upper"),
            InlineKeyboardButton(text="СБ", callback_data="weekday_saturday_upper")
        ],
        [
            InlineKeyboardButton(text="ПН", callback_data="weekday_monday_lower"),
            InlineKeyboardButton(text="ВТ", callback_data="weekday_tuesday_lower"),
            InlineKeyboardButton(text="СР", callback_data="weekday_wednesday_lower"),
            InlineKeyboardButton(text="ЧТ", callback_data="weekday_thursday_lower"),
            InlineKeyboardButton(text="ПТ", callback_data="weekday_friday_lower"),
            InlineKeyboardButton(text="СБ", callback_data="weekday_saturday_lower")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_room_weekday_buttons(room: str = None) -> InlineKeyboardMarkup:
    """Генерация кнопок дней недели с учетом аудитории"""
    buttons = [
        [
            InlineKeyboardButton(text="ПН", callback_data=f"roomday_monday_upper_{room}"),
            InlineKeyboardButton(text="ВТ", callback_data=f"roomday_tuesday_upper_{room}"),
            InlineKeyboardButton(text="СР", callback_data=f"roomday_wednesday_upper_{room}"),
            InlineKeyboardButton(text="ЧТ", callback_data=f"roomday_thursday_upper_{room}"),
            InlineKeyboardButton(text="ПТ", callback_data=f"roomday_friday_upper_{room}"),
            InlineKeyboardButton(text="СБ", callback_data=f"roomday_saturday_upper_{room}"),
        ],
        [
            InlineKeyboardButton(text="ПН", callback_data=f"roomday_monday_lower_{room}"),
            InlineKeyboardButton(text="ВТ", callback_data=f"roomday_tuesday_lower_{room}"),
            InlineKeyboardButton(text="СР", callback_data=f"roomday_wednesday_lower_{room}"),
            InlineKeyboardButton(text="ЧТ", callback_data=f"roomday_thursday_lower_{room}"),
            InlineKeyboardButton(text="ПТ", callback_data=f"roomday_friday_lower_{room}"),
            InlineKeyboardButton(text="СБ", callback_data=f"roomday_saturday_lower_{room}"),
        ],
        [InlineKeyboardButton(text="Назад", callback_data="room_schedule_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_teacher_weekday_buttons(teacher_name: str) -> InlineKeyboardMarkup:
    """Клавиатура для выбора дня недели преподавателя"""
    buttons = [
        [
            InlineKeyboardButton(text="ПН", callback_data=f"teacherday_monday_upper_{teacher_name}"),
            InlineKeyboardButton(text="ВТ", callback_data=f"teacherday_tuesday_upper_{teacher_name}"),
            InlineKeyboardButton(text="СР", callback_data=f"teacherday_wednesday_upper_{teacher_name}"),
            InlineKeyboardButton(text="ЧТ", callback_data=f"teacherday_thursday_upper_{teacher_name}"),
            InlineKeyboardButton(text="ПТ", callback_data=f"teacherday_friday_upper_{teacher_name}"),
            InlineKeyboardButton(text="СБ", callback_data=f"teacherday_saturday_upper_{teacher_name}"),
        ],
        [
            InlineKeyboardButton(text="ПН", callback_data=f"teacherday_monday_lower_{teacher_name}"),
            InlineKeyboardButton(text="ВТ", callback_data=f"teacherday_tuesday_lower_{teacher_name}"),
            InlineKeyboardButton(text="СР", callback_data=f"teacherday_wednesday_lower_{teacher_name}"),
            InlineKeyboardButton(text="ЧТ", callback_data=f"teacherday_thursday_lower_{teacher_name}"),
            InlineKeyboardButton(text="ПТ", callback_data=f"teacherday_friday_lower_{teacher_name}"),
            InlineKeyboardButton(text="СБ", callback_data=f"teacherday_saturday_lower_{teacher_name}"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# --- Меню выбора института ---
def get_institutes_menu() -> InlineKeyboardMarkup:
    """Клавиатура с выбором института (Inline)"""
    institutes = ["ГИ", "ИБМИ", "ИБО", "ИЭУ", "ИФКИ", "ИКН", "ИНМ", "ИТ", "ПИШ МАСТ"]
    buttons = []
    
    # Разбиваем на ряды по 3 кнопки
    for i in range(0, len(institutes), 3):
        row = institutes[i:i+3]
        buttons.append([InlineKeyboardButton(text=inst, callback_data=f"inst_{inst}") for inst in row])
    
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_years_menu(institute: str) -> InlineKeyboardMarkup:
    """Клавиатура с выбором курса (Inline)"""
    with open("data/groups.json", "r", encoding="utf-8") as f:
        groups_data = json.load(f)
    
    years = list(groups_data.get(institute, {}).keys())
    buttons = []
    
    # Разбиваем на ряды по 2 кнопки
    for i in range(0, len(years), 2):
        row = years[i:i+2]
        buttons.append([InlineKeyboardButton(text=year, callback_data=f"year_{year}") for year in row])
    
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="back_to_inst")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_groups_menu(institute: str, year: str) -> InlineKeyboardMarkup:
    """Клавиатура с выбором группы (Inline)"""
    with open("data/groups.json", "r", encoding="utf-8") as f:
        groups_data = json.load(f)
    
    groups = groups_data.get(institute, {}).get(year, [])
    buttons = []
    
    # Разбиваем на ряды по 3 кнопки
    for i in range(0, len(groups), 3):
        row = groups[i:i+3]
        buttons.append([InlineKeyboardButton(text=group, callback_data=f"group_{group}") for group in row])
    
    buttons.append([InlineKeyboardButton(text="Назад", callback_data=f"back_to_years_{institute}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_subgroups_menu() -> InlineKeyboardMarkup:
    """Клавиатура с выбором подгруппы (Inline)"""
    buttons = [
        [InlineKeyboardButton(text="1", callback_data="subgroup_1")],
        [InlineKeyboardButton(text="2", callback_data="subgroup_2")],
        [InlineKeyboardButton(text="Все", callback_data="subgroup_all")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_groups")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_save_confirmation_menu() -> InlineKeyboardMarkup:
    """Клавиатура с подтверждением сохранения (Inline)"""
    buttons = [
        [InlineKeyboardButton(text="Да", callback_data="save_yes")],
        [InlineKeyboardButton(text="Нет", callback_data="save_no")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_subgroups")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
