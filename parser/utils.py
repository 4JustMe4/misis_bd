def iterThrow(byGroupe, func):
    result = {}
    for group, shedule in byGroupe.items():
        for subGroup, days in shedule.items():
            for day, lessons in days.items():
                for lesson, types in lessons.items():
                    for type, content in types.items():
                        location = content["place"]
                        subject = content["subject"]
                        func(result, group, subGroup, day, lesson, type, location, subject)
    return result
