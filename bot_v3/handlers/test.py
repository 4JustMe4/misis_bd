from loader import loadData


def get_session_schedule(group_name: str) -> str:
    data = loadData("session")
    
    if group_name not in data:
        return f"❌ Расписание сессии для группы {group_name} не найдено."

    result_lines = [f"📚 Расписание летней сессии для группы {group_name}:"]
    subgroup_data = data[group_name]

    for subgroup, dates in subgroup_data.items():
        for date, halves in dates.items():
            for half_day, session in halves.items():
                subject = session.get('subject', '').strip()
                place = session.get('place', '').strip()

                if subject:  # выводим только если предмет не пустой
                    half_str = "первая половина дня" if half_day == "1" else "вторая половина дня"
                    place_str = place if place else "аудитория не указана"
                    result_lines.append(
                        f"👾 {subject} {date}, {half_str} {place_str}"
                    )

    if len(result_lines) == 1:
        return f"ℹ️ Для группы {group_name} пока нет информации о летней сессии."
    
    return "\n".join(result_lines)

print(get_session_schedule("БПМ-21-1"))