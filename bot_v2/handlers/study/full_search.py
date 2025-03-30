from aiogram import Router, F
from aiogram.types import Message
from datetime import datetime
from aiogram import Router, types, F
from aiogram.types import Message
import json

from .current_schedule import get_day, get_schedule
from .common import user_profile, user_selections, get_day

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
    #Первая функция, реагирующая на запрос 'Поиск расписания'#
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
        reply_markup=get_subgroups_menu()
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
async def confirm_save(call: types.CallbackQuery):
    today = get_day()
    current_week = "upper" if (datetime.today().isocalendar()[1] % 2) != 0 else "lower"

    #Обработка подтверждения сохранения#
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
        reply_markup=get_subgroups_menu()
    )
