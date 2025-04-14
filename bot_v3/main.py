import asyncio
import logging
from aiogram import F, Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
# проверка подключения к гиту
# ну и еще
from config import BOT_TOKEN
from handlers.keyboards import get_main_menu, get_class_schedule_menu

# Импортируем все модули
from handlers.study import router as study_router
from handlers.user_profile.profile_handlers import router as profile_router
# from handlers.exams import router as exams_router  # Будущий модуль
# from handlers.retakes import router as retakes_router  # Будущий модуль

# Настройка логирования
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Подключаем роутеры
dp.include_router(profile_router)  # Профиль пользователя
dp.include_router(study_router)    # Расписание занятий
# dp.include_router(exams_router)  # Экзамены
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

async def main():
    print("Бот запущен...")
    await set_bot_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())