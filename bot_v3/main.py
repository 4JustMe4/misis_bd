import asyncio
import logging
from aiogram import F, Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from handlers.user_profile.profile_keyboards import get_profile_keyboard
from handlers.user_profile.profile_utils import get_profile_text
from config import BOT_TOKEN
from handlers.keyboards import get_main_menu, get_class_schedule_menu

# Импортируем все модули
from handlers.study import router as study_router
from handlers.user_profile.profile_handlers import router as profile_router
from handlers.exams.exams_handlers import router as exams_router
# from handlers.retakes import router as retakes_router  # Будущий модуль

# Настройка логирования
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Подключаем роутеры
dp.include_router(profile_router)  # Профиль пользователя
dp.include_router(exams_router)    # Экзамены
dp.include_router(study_router)    # Расписание занятий
# dp.include_router(retakes_router)  # Пересдачи

# Стек для возврата на предыдущий уровень
menu_stack = []

# Установка команд бота
async def set_bot_commands(bot: Bot):
    commands = [
        types.BotCommand(command="start", description="Начало работы"),
        types.BotCommand(command="profile", description="Управление профилем"),
        types.BotCommand(command="help", description="Помощь")
    ]
    await bot.set_my_commands(commands)

# Хэндлеры
@dp.message(Command("start"))
async def cmd_start(message: Message):
    menu_stack.clear()
    await message.answer(
        "Привет! Я бот расписания МИСиС.\n"
        "Используй команду /profile для настройки своего профиля.",
        reply_markup=get_main_menu()
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📌 Доступные команды:\n\n"
        "/start - Перезапустить бота\n"
        "/profile - Настроить профиль\n"
        "/help - Получить помощь\n\n"
        "Основные функции доступны через кнопки меню"
    )

@dp.message(Command("profile"))
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

@dp.message(F.text == "Назад")
async def go_back(message: types.Message):
    """Обработчик кнопки Назад"""
    if menu_stack:
        previous_menu = menu_stack.pop()
        await message.answer("Возврат в предыдущее меню", reply_markup=previous_menu)
    else:
        await message.answer("Вы в главном меню", reply_markup=get_main_menu())

@dp.message(F.text == "Расписание занятий")
async def class_schedule(message: types.Message):
    """Переход в подменю расписания занятий"""
    menu_stack.append(get_main_menu())
    await message.answer(
        "Выберите тип расписания:",
        reply_markup=get_class_schedule_menu()
    )

@dp.message(F.text == "Расписание сессии")
async def session_schedule(message: types.Message):
    """Переход в подменю расписания сессии"""
    from handlers.exams.exams_handlers import get_session_menu
    menu_stack.append(get_main_menu())
    await message.answer(
        "Выберите действие:",
        reply_markup=get_session_menu()
    )

"""@dp.message()
async def handle_message(message: Message):
    #Основной обработчик сообщений с быстрым поиском
    text = message.text
    
    # Пропускаем сообщения, которые уже обработаны другими хэндлерами
    if text in ["Расписание занятий", "Расписание сессии", "Назад"]:
        return
    
    # Быстрый поиск (из handlers.study)
    from handlers.study.quick_search import detect_and_search
    search_result = detect_and_search(text)
    
    if search_result["matches"]:
        if search_result["type"] == "teacher":
            await message.answer(f"Найдены преподаватели:\n" + "\n".join(search_result["matches"]))
        elif search_result["type"] == "group":
            await message.answer(f"Найдены группы:\n" + "\n".join(search_result["matches"]))
        elif search_result["type"] == "room":
            await message.answer(f"Найдены аудитории:\n" + "\n".join(search_result["matches"]))
    else:
        await message.answer("Ничего не найдено. Попробуйте уточнить запрос.")"""

async def main():
    print("Бот запущен...")
    await set_bot_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())