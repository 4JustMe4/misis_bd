from datetime import datetime, timedelta
from user_profile.profile_utils import load_user_profile

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
