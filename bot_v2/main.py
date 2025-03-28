import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message

from config import BOT_TOKEN
from handlers.keyboards import get_main_menu, get_class_schedule_menu

from handlers.study import router as study_router
#from handlers.exams import router as exams_router  # Будущий модуль
#from handlers.retakes import router as retakes_router  # Будущий модуль

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(study_router)
#dp.include_router(exams_router)
#dp.include_router(retakes_router)

# Стек для возврата на предыдущий уровень
menu_stack = []

@dp.message(Command("start"))
async def cmd_start(message: Message):
    menu_stack.clear()
    await message.answer("Привет! Я бот расписания МИСиС.", reply_markup=get_main_menu())

@dp.message(lambda message: message.text == "Назад")
async def go_back(message: types.Message):
    #Возврат на предыдущий уровень.#
    if menu_stack:
        previous_menu = menu_stack.pop()
        await message.answer("Возврат в предыдущее меню", reply_markup=previous_menu)
    else:
        await message.answer("Вы в главном меню", reply_markup=get_main_menu())

@dp.message(lambda message: message.text == "Расписание занятий")
async def class_schedule(message: types.Message):
    #Переход в подменю расписания занятий.#
    menu_stack.append(get_main_menu())
    await message.answer("Выберите тип расписания:", reply_markup=get_class_schedule_menu())

async def main():
    print("Бот запущен...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())