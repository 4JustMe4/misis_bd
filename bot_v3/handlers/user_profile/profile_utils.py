import json
import logging
import re
from typing import Dict, Union
from pathlib import Path
from aiogram import Bot
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest

from handlers.study.common import loadData


def load_user_profile(user_id: int) -> Dict:
    try:
        return loadData("users").get(str(user_id), {
            "main_group": None,
            "subgroup": "all",
            "english_group": None,
            "saved_groups": []
        })
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "main_group": None,
            "subgroup": "all", 
            "english_group": None,
            "saved_groups": []
        }


def save_user_profile(user_id: int, profile: Dict):
    """Гарантированно сохраняет профиль пользователя"""
    try:
        # Создаем директорию, если не существует
        Path("data").mkdir(exist_ok=True)
        
        # Загружаем текущие данные
        try:
            users = loadData("users")
        except (FileNotFoundError, json.JSONDecodeError):
            users = {}
        
        # Обязательные поля профиля
        required_fields = {
            "main_group": "не выбрана",
            "subgroup": "all",
            "english_group": None,
            "saved_groups": []
        }
        
        # Объединяем с defaults
        full_profile = {**required_fields, **profile}
        
        # Проверка формата группы
        if full_profile["main_group"] and not re.match(r"^[А-Я]{2,}-\d{2,}-\d$", full_profile["main_group"]):
            raise ValueError(f"Некорректный формат группы: {full_profile['main_group']}")
        
        # Сохраняем
        users[str(user_id)] = full_profile
        
        # Atomic write
        temp_file = "data/users.temp.json"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
        
        # Переименовываем (atomic операция)
        Path(temp_file).replace("data/users.json")
        
        # Логируем успех
        logging.info(f"Сохранен профиль для {user_id}: группа {full_profile['main_group']}")
        
    except Exception as e:
        logging.error(f"Ошибка сохранения профиля {user_id}: {e}")
        raise

    # Проверка что данные действительно сохранились
    def verify_profile_saved(user_id: int, expected_group: str) -> bool:
        try:
            data = loadData("users")
            return data.get(str(user_id), {}).get("main_group") == expected_group
        except:
            return False
    

def validate_english_group(group_num: str) -> bool:
    try:
        return group_num in loadData("english_groups")
    except (FileNotFoundError, json.JSONDecodeError):
        return False
    


def get_subgroups_for_group(group: str) -> list:
    """Возвращает список доступных подгрупп для указанной группы"""
    try:
        schedule = loadData("schedule")
        
        if group not in schedule:
            return ["1", "2"]  # Значения по умолчанию
            
        # Получаем все подгруппы для группы
        subgroups = list(schedule[group].keys())
        
        # Фильтруем только цифровые подгруппы
        valid_subgroups = [sub for sub in subgroups if sub.isdigit()]
        
        return sorted(valid_subgroups) if valid_subgroups else ["1", "2"]
        
    except Exception as e:
        logging.error(f"Ошибка при определении подгрупп: {e}")
        return ["1", "2"]  # Фолбэк значения
    

async def clear_previous_bot_messages(call: CallbackQuery, keep_last: int = 1):
    """Удаляет предыдущие сообщения бота, оставляя только последние N"""
    try:
        messages = await Bot.get_current().get_chat_administrators(call.message.chat.id)
        bot_id = (await Bot.get_current().me).id
        
        async for msg in Bot.get_current().get_chat_history(call.message.chat.id):
            if msg.from_user.id == bot_id and msg.message_id != call.message.message_id:
                await msg.delete()
                keep_last -= 1
                if keep_last <= 0:
                    break
    except Exception as e:
        logging.error(f"Ошибка при очистке сообщений: {e}")

async def get_profile_text(user_id: int) -> str:
    """Генерирует текст профиля без отправки сообщения"""
    profile = load_user_profile(user_id)
    return (
        f"📌 Ваш профиль\n\n"
        f"▪ Основная группа: {profile['main_group'] or 'не выбрана'} ({profile['subgroup']})\n"
        f"▪ Группа по английскому: {profile['english_group'] or '-'}\n"
        f"▪ Сохранённые группы: {len(profile['saved_groups'])}"
    )


async def delete_previous_bot_messages(call: CallbackQuery, keep_last: int = 1):
    """Удаляет предыдущие сообщения бота"""
    try:
        bot = Bot.get_current()
        messages = []
        
        async for message in bot.get_chat_history(call.message.chat.id):
            if message.from_user.id == bot.id and message.message_id != call.message.message_id:
                messages.append(message)
                if len(messages) >= 10:  # Лимит для безопасности
                    break
        
        # Удаляем все кроме последнего N сообщений
        for msg in messages[:-keep_last]:
            try:
                await msg.delete()
            except TelegramBadRequest:
                continue
                
    except Exception as e:
        logging.error(f"Ошибка при удалении сообщений: {e}")


def validate_profile(profile: dict) -> bool:
    """Проверяет целостность данных профиля"""
    return all(
        key in profile 
        for key in ["main_group", "subgroup", "english_group", "saved_groups"]
    )

async def debug_user_profile(user_id: int):
    """Логирование для отладки"""
    profile = load_user_profile(user_id)
    logging.info(
        f"DEBUG PROFILE FOR {user_id}:\n"
        f"Main: {profile.get('main_group')}\n"
        f"Sub: {profile.get('subgroup')}\n"
        f"English: {profile.get('english_group')}\n"
        f"Saved: {len(profile.get('saved_groups', []))}"
    )


async def delete_previous_messages(call: CallbackQuery, keep_last: int = 1):
    """Удаляет предыдущие сообщения бота"""
    try:
        bot = Bot.get_current()
        messages = []
        
        async for msg in bot.get_chat_history(call.message.chat.id):
            if msg.from_user.id == bot.id and msg.message_id != call.message.message_id:
                messages.append(msg)
                if len(messages) >= 10:  # Лимит для безопасности
                    break
        
        for msg in messages[:-keep_last]:
            try:
                await msg.delete()
            except:
                continue
                
    except Exception as e:
        logging.error(f"Ошибка удаления сообщений: {e}")

def verify_group_change(user_id: int, expected_group: str) -> bool:
    """Проверяет фактическое изменение группы"""
    profile = load_user_profile(user_id)
    return profile.get("main_group") == expected_group

async def force_message_update(target: Union[Message, CallbackQuery], text: str, markup=None):
    """Гарантированное обновление сообщения"""
    try:
        if isinstance(target, CallbackQuery):
            await target.message.delete()
            await target.message.answer(text, reply_markup=markup)
        else:
            await target.answer(text, reply_markup=markup)
    except Exception as e:
        logging.error(f"Force update failed: {e}")
        raise