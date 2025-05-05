from datetime import datetime, timedelta
from handlers.user_profile.profile_utils import load_user_profile
import json
from parser.mongo import loadJsonFromMongo

def get_user_profile(user_id: int):
    """Загружает профиль пользователя"""
    return load_user_profile(user_id)

user_selections = {}

def get_day():
    day = datetime.today().strftime("%A")
    days = {
        "Monday": "Понедельник",
        "Tuesday": "Вторник",
        "Wednesday": "Среда",
        "Thursday": "Четверг",
        "Friday": "Пятница",
        "Saturday": "Суббота",
        "Sunday": "Воскресенье"
    }
    return days.get(day, "Неизвестный день")

def get_tomorrow():
    day = datetime.today()
    day = day + timedelta(days=1)
    days = {
        "Monday": "Понедельник",
        "Tuesday": "Вторник",
        "Wednesday": "Среда",
        "Thursday": "Четверг",
        "Friday": "Пятница",
        "Saturday": "Суббота",
        "Sunday": "Воскресенье"
    }
    return days.get(day.strftime("%A"), "Неизвестный день")


def loadData(name):
    data = loadJsonFromMongo(name)
    if data is not None:
        return data
    else:
        try:
            with open(f"data/{name}.json", "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as e:
            print(f"Ошибка при чтении локального файла {name}.json: {e}")
            return None
