import logging
from aiogram import Router, F
from aiogram.types import Message
from datetime import datetime
from aiogram import Router, types, F
from aiogram.types import Message, CallbackQuery
import json

from handlers.user_profile.profile_handlers import show_profile
from handlers.user_profile.profile_keyboards import get_profile_keyboard

from .current_schedule import get_day, get_schedule
from .common import user_selections, get_day
from handlers.user_profile.profile_utils import get_profile_text, load_user_profile, save_user_profile

from handlers.keyboards import (
    get_class_schedule_menu,
    get_institutes_menu,
    get_years_menu,
    get_groups_menu,
    get_subgroups_menu,
    get_save_confirmation_menu,
    get_weekday_buttons,
    get_full_schedule_menu
)



router = Router()



# Хэндлеры
@router.message(F.text == "Поиск расписания")
async def full_schedule_start(message: Message):
    #Первая функция, реагирующая на запрос 'Полное расписание'#
    await message.answer(
        "Выберите тип расписания:",
        reply_markup=get_full_schedule_menu()  # Показывает меню с 3 вариантами + назад
    )


@router.callback_query(F.data.startswith("inst_"))
async def choose_institute(call: types.CallbackQuery):
    #Обработка выбора института#
    institute = call.data.split("_")[1]
    user_selections[call.from_user.id] = {"institute": institute}
    
    await call.message.edit_text(
        f"Выберите курс обучения в институте {institute}:",
        reply_markup=get_years_menu(institute)
    )


@router.callback_query(F.data.startswith("year_"))
async def choose_year(call: types.CallbackQuery):
    #Обработка выбора курса#
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
    #Обработка выбора группы#
    group = call.data.split("_")[1]
    user_id = call.from_user.id
    
    if user_id not in user_selections or "year" not in user_selections[user_id]:
        await call.answer("Пожалуйста, начните выбор сначала.")
        return
    
    user_selections[user_id]["group"] = group
    institute = user_selections[user_id]["institute"]

    await call.message.edit_text(
        f"Выберите подгруппу для группы {group}, {institute}:",
        reply_markup=get_subgroups_menu(group)
    )


@router.callback_query(F.data.startswith("subgroup_"))
async def choose_subgroup(call: types.CallbackQuery):
    #Обработка выбора подгруппы#
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
async def confirm_save(call: CallbackQuery):
    """Обработчик сохранения группы"""
    try:
        action = call.data.split("_")[1]
        user_id = call.from_user.id
        
        if user_id not in user_selections or "selected_group" not in user_selections[user_id]:
            await call.answer("❌ Данные утеряны, начните сначала")
            return
            
        profile = load_user_profile(user_id)
        selected = user_selections[user_id]["selected_group"]
        
        if action == "yes":
            if any(g["group"] == selected["group"] for g in profile["saved_groups"]):
                await call.answer("⚠️ Группа уже в избранном")
            else:
                group_data = {
                    "group": selected["group"],
                    "subgroup": selected["subgroup"],
                    "institute": user_selections[user_id].get("institute", ""),
                    "added_at": datetime.now().strftime("%d.%m.%Y %H:%M")
                }
                profile["saved_groups"].append(group_data)
                save_user_profile(user_id, profile)
                await call.answer("✅ Группа сохранена!")
        
        try:
            await call.message.delete()
        except:
            pass
            
        # Показываем только расписание без профиля
        today = get_day()
        current_week = "upper" if (datetime.now().isocalendar()[1] % 2) != 0 else "lower"
        
        with open("data/schedule.json", "r", encoding="utf-8") as f:
            schedule = json.load(f)
            
        await call.message.answer(
            text=get_schedule(selected["group"], selected["subgroup"], current_week, today, schedule),
            reply_markup=get_weekday_buttons(),
            parse_mode="HTML"
        )
        
    except json.JSONDecodeError:
        await call.answer("❌ Ошибка загрузки расписания")
    except Exception as e:
        logging.error(f"Save confirmation error: {e}")
        await call.answer("⚠️ Ошибка сохранения")



# Навигация назад
@router.callback_query(F.data == "back_to_main")
async def back_to_main(call: types.CallbackQuery):
    """Возврат в главное меню с сохранением inline-клавиатуры"""
    await call.message.edit_text(
        "Выберите тип расписания:",
        reply_markup=get_full_schedule_menu()  # Возвращаемся к первому inline-меню
    )


@router.callback_query(F.data == "back_to_inst")
async def back_to_institutes(call: types.CallbackQuery):
    #Возврат к выбору института#
    await call.message.edit_text(
        "Выберите институт:",
        reply_markup=get_institutes_menu()
    )


@router.callback_query(F.data.startswith("back_to_years_"))
async def back_to_years(call: types.CallbackQuery):
    #Возврат к выбору курса#
    institute = call.data.split("_")[-1]
    await call.message.edit_text(
        f"Выберите курс обучения в институте {institute}:",
        reply_markup=get_years_menu(institute)
    )


@router.callback_query(F.data == "back_to_groups")
async def back_to_groups(call: types.CallbackQuery):
    #Возврат к выбору группы#
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
    #Возврат к выбору подгруппы#
    user_id = call.from_user.id
    if user_id not in user_selections or "group" not in user_selections[user_id]:
        await call.answer("Пожалуйста, начните выбор сначала.")
        return
    
    group = user_selections[user_id]["group"]
    institute = user_selections[user_id]["institute"]
    
    await call.message.edit_text(
        f"Выберите подгруппу для группы {group}, {institute}:",
        reply_markup=get_subgroups_menu(group)
    )