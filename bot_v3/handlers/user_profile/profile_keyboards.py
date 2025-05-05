from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from handlers.study.common import loadData
from handlers.user_profile.profile_utils import get_subgroups_for_group

# Префиксы для изоляции колбэков
PR_ = "pr_"  # Основные действия профиля
MG_ = "mg_"  # Основная группа
SG_ = "sg_"  # Сохранённые группы

def get_profile_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура основного меню профиля"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Основная группа", callback_data=MG_ + "start")],
        [InlineKeyboardButton(text="🔢 Подгруппа", callback_data=PR_ + "change_subgroup")],
        [InlineKeyboardButton(text="🇬🇧 Английский", callback_data=PR_ + "set_english")],
        [InlineKeyboardButton(text="📚 Избранные группы", callback_data=PR_ + "manage_saved")]
    ])

def get_english_group_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для ввода группы по английскому"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ Назад", callback_data=PR_ + "back")]
    ])

def get_manage_saved_groups_keyboard(groups: list, is_remove_mode: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура управления сохранёнными группами"""
    buttons = []
    for i, g in enumerate(groups):
        btn_text = f"{'❌ ' if is_remove_mode else ''}{i+1}. {g['group']} ({g['subgroup']})"
        btn_data = PR_ + f"{'remove_' if is_remove_mode else 'show_'}{i}"
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=btn_data)])
    
    if not is_remove_mode:
        buttons.append([
            InlineKeyboardButton(text="➕ Добавить", callback_data=SG_ + "start"),
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=PR_ + "start_remove")
        ])
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data=PR_ + "back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_institutes_menu(context: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора института с кнопками в 3 колонки"""
    prefix = MG_ if context == "main" else SG_
    institutes = list(loadData("groups").keys())
        
    
    buttons = []
    for i in range(0, len(institutes), 3):
        row = institutes[i:i+3]
        buttons.append([
            InlineKeyboardButton(text=inst, callback_data=prefix + f"inst_{inst}") 
            for inst in row
        ])
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data=PR_ + "back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_years_menu(institute: str, context: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора курса с кнопками в 2 колонки"""
    prefix = MG_ if context == "main" else SG_
    years = list(loadData("groups").get(institute, {}).keys())
    
    buttons = []
    for i in range(0, len(years), 2):
        row = years[i:i+2]
        buttons.append([
            InlineKeyboardButton(text=year, callback_data=prefix + f"year_{year}") 
            for year in row
        ])
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data=prefix + "back_inst")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_groups_menu(institute: str, year: str, context: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора группы с кнопками в 3 колонки"""
    prefix = MG_ if context == "main" else SG_
    groups = loadData("groups").get(institute, {}).get(year, [])
    
    buttons = []
    for i in range(0, len(groups), 3):
        row = groups[i:i+3]
        buttons.append([
            InlineKeyboardButton(text=group, callback_data=prefix + f"group_{group}") 
            for group in row
        ])
    
    buttons.append([InlineKeyboardButton(
        text="🔙 Назад", 
        callback_data=prefix + f"back_year_{institute}"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_subgroups_menu(group: str, context: str) -> InlineKeyboardMarkup:
    """Создаёт динамическую клавиатуру подгрупп"""
    prefix = MG_ if context == "main" else SG_
    
    # Получаем актуальные подгруппы
    subgroups = get_subgroups_for_group(group)
    
    # Создаём кнопки для подгрупп
    buttons = [
        [InlineKeyboardButton(
            text=f"Подгруппа {sub}",
            callback_data=f"{prefix}sub_{sub}"
        )]
        for sub in subgroups
    ]
    
    # Добавляем кнопку "Все" если подгрупп больше 1
    if len(subgroups) > 1:
        buttons.append([InlineKeyboardButton(
            text="Все подгруппы",
            callback_data=f"{prefix}sub_all"
        )])
    
    # Добавляем кнопку назад с учётом контекста
    back_button = [InlineKeyboardButton(
        text="🔙 Назад",
        callback_data=f"{prefix}back_group_{group.split('-')[0]}"
    )]
    buttons.append(back_button)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)