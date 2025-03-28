from datetime import datetime, timedelta

user_profile = {
    "group": "БПМ-21-1",
    "subgroup": "all",
    "saved_groups": []
}

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

