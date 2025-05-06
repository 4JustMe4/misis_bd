import asyncio
from datetime import datetime
import logging
from aiogram import Bot, Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from typing import Dict, Optional, Union

from handlers.loader import loadData
from handlers.keyboards import get_weekday_buttons
from handlers.study.common import get_day
from handlers.study.current_schedule import get_schedule
from aiogram.exceptions import TelegramBadRequest


from .profile_utils import clear_previous_bot_messages, delete_previous_bot_messages, delete_previous_messages, get_profile_text, get_subgroups_for_group, load_user_profile, save_user_profile, validate_english_group
from .profile_keyboards import (
    get_profile_keyboard,
    get_manage_saved_groups_keyboard,
    get_english_group_keyboard,
    get_institutes_menu,
    get_years_menu,
    get_groups_menu,
    get_subgroups_menu,
    PR_, MG_, SG_
)

router = Router()
user_selections = {}

async def show_profile(target: Union[Message, CallbackQuery], success_message: str = ""):
    """Унифицированная функция показа профиля"""
    try:
        profile_text = await get_profile_text(target.from_user.id)
        if success_message:
            profile_text = f"✅ {success_message}\n\n{profile_text}"
        
        if isinstance(target, CallbackQuery):
            try:
                await target.message.edit_text(
                    text=profile_text,
                    reply_markup=get_profile_keyboard()
                )
            except TelegramBadRequest:
                await target.message.answer(
                    text=profile_text,
                    reply_markup=get_profile_keyboard()
                )
        else:
            await target.answer(
                text=profile_text,
                reply_markup=get_profile_keyboard()
            )
    except Exception as e:
        logging.error(f"Ошибка в show_profile: {e}")
        await target.answer("⚠️ Не удалось загрузить профиль")
    





async def _delete_previous_message(call: CallbackQuery):
    """Безопасное удаление предыдущего сообщения"""
    try:
        await call.message.delete()
    except:
        pass

async def _show_updated_profile(call: CallbackQuery):
    """Показ актуального профиля с очисткой истории"""
    try:
        # Сначала удаляем старое сообщение
        await _delete_previous_message(call)
        
        # Затем отправляем новое с актуальными данными
        await call.message.answer(
            text=await get_profile_text(call.from_user.id),
            reply_markup=get_profile_keyboard()
        )
    except Exception as e:
        logging.error(f"Profile update error: {e}")
        await call.answer("✅ Данные сохранены, но не удалось обновить вид")


async def show_saved_groups(call: CallbackQuery, is_remove_mode: bool = False):
    """Показывает список сохраненных групп"""
    try:
        profile = load_user_profile(call.from_user.id)
        
        text = "📭 У вас пока нет сохранённых групп" if not profile["saved_groups"] else (
            "📚 Ваши сохранённые группы:\n" + 
            "\n".join(f"{i+1}. {g['group']} ({g['subgroup']})" 
                     for i, g in enumerate(profile["saved_groups"]))
        )
        
        # Если это CallbackQuery, редактируем существующее сообщение
        if isinstance(call, CallbackQuery):
            try:
                await call.message.edit_text(
                    text=text,
                    reply_markup=get_manage_saved_groups_keyboard(
                        profile["saved_groups"],
                        is_remove_mode
                    )
                )
            except TelegramBadRequest:
                await call.message.answer(
                    text=text,
                    reply_markup=get_manage_saved_groups_keyboard(
                        profile["saved_groups"],
                        is_remove_mode
                    )
                )
        else:
            await call.answer(
                text=text,
                reply_markup=get_manage_saved_groups_keyboard(
                    profile["saved_groups"],
                    is_remove_mode
                )
            )
    except Exception as e:
        logging.error(f"Show groups error: {e}")
        await call.answer("⚠️ Ошибка загрузки списка групп")


async def save_group_selection(
    call: CallbackQuery, 
    group_data: Dict, 
    is_main_group: bool
):
    """Сохраняет выбранную группу (основную или в избранное)"""
    user_id = call.from_user.id
    profile = load_user_profile(user_id)
    
    if is_main_group:
        profile.update({
            "main_group": group_data["group"],
            "subgroup": group_data["subgroup"]
        })
    else:
        # Проверяем, нет ли уже такой группы в избранном
        if not any(g["group"] == group_data["group"] for g in profile["saved_groups"]):
            profile["saved_groups"].append(group_data)
            await call.answer(f"✅ Группа {group_data['group']} сохранена!")
        else:
            await call.answer("⚠️ Эта группа уже есть в избранном")
    
    save_user_profile(user_id, profile)
    await show_saved_groups(call)

@router.message(Command("profile"))
async def cmd_profile(message: Message):
    """Обработчик команды /profile с исправленной логикой"""
    try:
        # Всегда отправляем новое сообщение вместо редактирования
        await message.answer(
            text=await get_profile_text(message.from_user.id),
            reply_markup=get_profile_keyboard()
        )
    except Exception as e:
        logging.error(f"Ошибка в cmd_profile: {e}")
        await message.answer("⚠️ Не удалось загрузить профиль")


async def show_group_schedule(call: CallbackQuery, group: str, subgroup: str):
    """Показывает расписание для выбранной группы"""
    try:
        today = get_day()
        current_week = "upper" if (datetime.today().isocalendar()[1] % 2) != 0 else "lower"
        
        schedule_data = loadData("schedule")
        
        response = get_schedule(group, subgroup, current_week, today, schedule_data)
        
        await call.message.answer(
            f"📅 Расписание для {group} ({subgroup}):\n\n{response}",
            reply_markup=get_weekday_buttons(),
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Show group schedule error: {e}")
        await call.answer("⚠️ Ошибка загрузки расписания")


@router.callback_query(F.data.startswith(PR_))
async def handle_profile_actions(call: CallbackQuery):
    """Полный обработчик всех действий профиля"""
    try:
        action = call.data.replace(PR_, "")
        user_id = call.from_user.id
        profile = load_user_profile(user_id)

        # Удаляем предыдущее сообщение
        try:
            await call.message.delete()
        except:
            pass

        if action == "back":
            await show_profile(call)
            
        elif action == "change_subgroup":
            if not profile["main_group"]:
                await call.answer("❌ Сначала выберите основную группу!")
                await show_profile(call)
                return
                
            await call.message.answer(
                f"Выберите подгруппу для {profile['main_group']}:",
                reply_markup=get_subgroups_menu(profile["main_group"], "main")
            )
            
        elif action == "set_english":
            await call.message.answer(
                "Введите номер группы по английскому (3 цифры):\n\n"
                "Пример: 440, 441 или 442",
                reply_markup=get_english_group_keyboard()
            )
            
        elif action == "manage_saved":
            await show_saved_groups(call)
            
        elif action == "start_remove":
            await show_saved_groups(call, is_remove_mode=True)
            
        elif action.startswith("remove_"):
            group_idx = int(action.split("_")[1])
            if 0 <= group_idx < len(profile["saved_groups"]):
                removed_group = profile["saved_groups"].pop(group_idx)
                save_user_profile(user_id, profile)
                await call.answer(f"❌ Удалена группа {removed_group['group']}")
            await show_saved_groups(call)
            
        elif action.startswith("show_"):
            group_idx = int(action.split("_")[1])
            if 0 <= group_idx < len(profile["saved_groups"]):
                selected = profile["saved_groups"][group_idx]
                await show_group_schedule(
                    call,
                    selected["group"],
                    selected["subgroup"]
                )
                await show_saved_groups(call)
                
    except Exception as e:
        logging.error(f"Profile action error: {e}")
        await call.answer("⚠️ Ошибка обработки команды")
        await show_profile(call)




@router.callback_query(F.data == PR_ + "change_subgroup")
async def handle_change_subgroup(call: CallbackQuery):
    """Обработчик изменения подгруппы с чистым завершением"""
    try:
        profile = load_user_profile(call.from_user.id)
        
        if not profile["main_group"]:
            await call.answer("❌ Сначала выберите основную группу!")
            return
            
        # Удаляем предыдущее сообщение
        try:
            await call.message.delete()
        except:
            pass
            
        # Отправляем новое сообщение с выбором
        await call.message.answer(
            f"Выберите подгруппу для {profile['main_group']}:",
            reply_markup=get_subgroups_menu(profile["main_group"], "main")
        )
        
    except Exception as e:
        logging.error(f"Ошибка при изменении подгруппы: {e}")
        await call.answer("⚠️ Ошибка при изменении подгруппы")

@router.callback_query(F.data.startswith(MG_ + "sub_"))
async def handle_subgroup_selection(call: CallbackQuery):
    """Обработчик выбора подгруппы"""
    try:
        user_id = call.from_user.id
        subgroup = call.data.split("_")[-1]
        
        profile = load_user_profile(user_id)
        if not profile.get("main_group"):
            await call.answer("❌ Сначала выберите группу")
            return
            
        profile["subgroup"] = subgroup
        save_user_profile(user_id, profile)
        
        # Удаляем предыдущие сообщения процесса выбора
        await delete_previous_bot_messages(call)
        
        # Показываем обновленный профиль
        await show_profile(call, "Настройки сохранены")
        
    except Exception as e:
        logging.error(f"Subgroup selection error: {e}")
        await call.answer("⚠️ Ошибка сохранения подгруппы")


async def _delete_all_selection_messages(call: CallbackQuery):
    """Удаляет все сообщения процесса выбора группы"""
    try:
        bot = Bot.get_current()
        async for msg in bot.get_chat_history(call.message.chat.id):
            if msg.from_user.id == bot.id:
                await msg.delete()
                await asyncio.sleep(0.3)  # Задержка для избежания flood
    except Exception as e:
        logging.error(f"Message cleanup error: {e}")




@router.callback_query(F.data.startswith(MG_ + "group_"))
async def handle_group_selection(call: CallbackQuery):
    """Обработчик выбора группы с НЕМЕДЛЕННЫМ сохранением"""
    try:
        user_id = call.from_user.id
        group_name = call.data.split("_")[-1]
        
        # Сохраняем группу СРАЗУ
        profile = load_user_profile(user_id)
        profile["main_group"] = group_name  # Сохраняем без подгруппы
        save_user_profile(user_id, profile)
        
        # Обновляем временные данные
        if user_id not in user_selections:
            user_selections[user_id] = {}
        user_selections[user_id]["group"] = group_name
        
        # Получаем доступные подгруппы
        subgroups = get_subgroups_for_group(group_name)
        
        await call.message.edit_text(
            f"Выберите подгруппу для {group_name} (доступно {len(subgroups)}):",
            reply_markup=get_subgroups_menu(group_name, "main")
        )
        
        # Дополнительная проверка
        updated = load_user_profile(user_id)
        if updated["main_group"] != group_name:
            logging.error(f"ОШИБКА: Группа не сохранилась! Ожидалось {group_name}, получили {updated['main_group']}")
            
    except Exception as e:
        logging.error(f"Ошибка выбора группы: {e}")
        await call.answer("❌ Ошибка сохранения группы")


@router.callback_query(F.data.startswith(PR_ + "show_"))
async def handle_show_saved_group(call: CallbackQuery):
    """Обработчик просмотра расписания сохраненной группы"""
    try:
        group_idx = int(call.data.split("_")[1])
        profile = load_user_profile(call.from_user.id)
        
        if 0 <= group_idx < len(profile["saved_groups"]):
            selected = profile["saved_groups"][group_idx]
            
            # Сначала обновляем сообщение со списком групп
            await call.message.edit_text(
                text=f"📚 Ваши сохранённые группы:\n" +
                     "\n".join(f"{i+1}. {g['group']} ({g['subgroup']})" 
                              for i, g in enumerate(profile["saved_groups"])),
                reply_markup=get_manage_saved_groups_keyboard(profile["saved_groups"])
            )
            
            # Затем показываем расписание
            await show_group_schedule(call, selected["group"], selected["subgroup"])
            
    except Exception as e:
        logging.error(f"Show saved group error: {e}")
        await call.answer("⚠️ Ошибка загрузки расписания")
        await show_saved_groups(call)


@router.callback_query(F.data.startswith(MG_))
async def handle_main_group_flow(call: CallbackQuery):
    """Полный обработчик выбора основной группы с очисткой сообщений"""
    try:
        data_parts = call.data.replace(MG_, "").split("_")
        user_id = call.from_user.id
        
        # Инициализация временных данных
        if not user_selections.get(user_id):
            user_selections[user_id] = {"context": "main"}
        
        ###########################################
        # 1. Старт выбора основной группы
        ###########################################
        if data_parts[0] == "start":
            await call.message.edit_text(
                "Выберите институт для основной группы:",
                reply_markup=get_institutes_menu("main")
            )
            return
        
        ###########################################
        # 2. Выбор института
        ###########################################
        elif data_parts[0] == "inst":
            user_selections[user_id].update({
                "institute": data_parts[1],
                "context": "main"
            })
            
            await call.message.edit_text(
                f"Институт: {data_parts[1]}\nВыберите курс:",
                reply_markup=get_years_menu(data_parts[1], "main")
            )
            return
        
        ###########################################
        # 3. Выбор курса
        ###########################################
        elif data_parts[0] == "year":
            user_selections[user_id]["year"] = data_parts[1]
            
            await call.message.edit_text(
                f"Институт: {user_selections[user_id]['institute']}\n"
                f"Курс: {data_parts[1]}\n\n"
                "Выберите группу:",
                reply_markup=get_groups_menu(
                    user_selections[user_id]["institute"],
                    data_parts[1],
                    "main"
                )
            )
            return
        
        ###########################################
        # 4. Выбор группы
        ###########################################
        elif data_parts[0] == "group":
            user_selections[user_id]["group"] = data_parts[1]
            group_name = data_parts[1]
            
            # Получаем динамические подгруппы
            subgroups = get_subgroups_for_group(group_name)
            
            await call.message.edit_text(
                f"Группа: {group_name}\n"
                f"Доступно подгрупп: {len(subgroups)}\n\n"
                "Выберите подгруппу:",
                reply_markup=get_subgroups_menu(group_name, "main")
            )
            return
        
        ###########################################
        # 5. Финальный выбор подгруппы
        ###########################################
        elif data_parts[0] == "sub":
            # Проверяем, что группа была выбрана
            if "group" not in user_selections.get(user_id, {}):
                await call.answer("❌ Сначала выберите группу")
                return
                
            subgroup = data_parts[1]
            
            # Готовим данные для сохранения
            new_profile = {
                "main_group": user_selections[user_id]["group"],
                "subgroup": subgroup
            }
            
            # Сохраняем с проверкой
            try:
                save_user_profile(user_id, new_profile)
            except Exception as e:
                logging.error(f"Ошибка сохранения: {e}")
                await call.answer("❌ Ошибка сохранения")
                return
            
            # Удаляем временные данные
            user_selections.pop(user_id, None)
            
            # Показываем подтверждение
            await call.message.edit_text(
                f"✅ Основная группа установлена:\n"
                f"{new_profile['main_group']} ({new_profile['subgroup']})",
                reply_markup=get_profile_keyboard()
            )
            
            # Дополнительная проверка
            updated = load_user_profile(user_id)
            if updated["main_group"] != new_profile["main_group"]:
                logging.error(f"Расхождение данных! Ожидалось {new_profile['main_group']}, получили {updated['main_group']}")
        
        ###########################################
        # 6. Обработка кнопки "Назад"
        ###########################################
        elif data_parts[0] == "back":
            # Удаляем текущее сообщение
            try:
                await call.message.delete()
            except TelegramBadRequest:
                pass
            
            if data_parts[1] == "inst":
                await call.message.answer(
                    "Выберите институт:",
                    reply_markup=get_institutes_menu("main")
                )
            elif data_parts[1] == "year":
                institute = user_selections[user_id]["institute"]
                await call.message.answer(
                    f"Институт: {institute}\nВыберите курс:",
                    reply_markup=get_years_menu(institute, "main")
                )
            elif data_parts[1] == "group":
                institute = user_selections[user_id]["institute"]
                year = user_selections[user_id]["year"]
                await call.message.answer(
                    f"Институт: {institute}\nКурс: {year}\n\n"
                    "Выберите группу:",
                    reply_markup=get_groups_menu(institute, year, "main")
                )
            return
    
    except Exception as e:
        logging.error(f"Ошибка в handle_main_group_flow: {e}")
        try:
            await call.message.answer(
                "⚠️ Произошла ошибка при обновлении профиля\n"
                "Попробуйте снова через /profile"
            )
        except:
            pass
        

@router.callback_query(F.data.startswith(SG_))
async def handle_saved_groups_flow(call: CallbackQuery):
    """Обработчик выбора сохранённых групп"""
    data_parts = call.data.replace(SG_, "").split("_")
    user_id = call.from_user.id
    
    if not user_selections.get(user_id):
        user_selections[user_id] = {"context": "saved"}
    
    if data_parts[0] == "start":
        await call.message.edit_text(
            "Выберите институт:",
            reply_markup=get_institutes_menu("saved")
        )
    elif data_parts[0] == "inst":
        user_selections[user_id].update({
            "institute": data_parts[1],
            "context": "saved"
        })
        await call.message.edit_text(
            f"Институт {data_parts[1]}. Выберите курс:",
            reply_markup=get_years_menu(data_parts[1], "saved")
        )
    elif data_parts[0] == "year":
        user_selections[user_id]["year"] = data_parts[1]
        await call.message.edit_text(
            f"Выберите группу ({user_selections[user_id]['institute']}, {data_parts[1]} курс):",
            reply_markup=get_groups_menu(
                user_selections[user_id]["institute"],
                data_parts[1],
                "saved"
            )
        )
    elif data_parts[0] == "group":
        user_selections[user_id]["group"] = data_parts[1]
        await call.message.edit_text(
            f"Выберите подгруппу для {data_parts[1]}:",
            reply_markup=get_subgroups_menu(data_parts[1], "saved")
        )
    elif data_parts[0] == "sub":
        await save_group_selection(
            call,
            {
                "group": user_selections[user_id]["group"],
                "subgroup": data_parts[1],
                "institute": user_selections[user_id].get("institute")
            },
            is_main_group=False
        )

@router.message(F.text.regexp(r"^\d{3}$"))
async def handle_english_group_input(message: Message):
    """Обработчик ввода группы по английскому"""
    if not validate_english_group(message.text):
        await message.answer(
            "❌ Группа не найдена. Доступные: 440, 441, 442",
            reply_markup=get_english_group_keyboard()
        )
        return
    
    profile = load_user_profile(message.from_user.id)
    profile["english_group"] = message.text
    save_user_profile(message.from_user.id, profile)
    await show_profile(message)