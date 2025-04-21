from utils import iterThrow


def updLocation(byLocation, group, subGroup, day, lesson, type, location, subject):
    if location == "":
        return
    if not location in byLocation:
        byLocation[location] = {}

    curLocation = byLocation[location]
    if not day in curLocation:
        curLocation[day] = {}

    curDay = curLocation[day]
    if not lesson in curDay:
        curDay[lesson] = {}

    curLesson = curDay[lesson]
    if not type in curLesson:
        curLesson[type] = { "subjects": {}}

    curType = curLesson[type]
    if not subject in curType["subjects"]:
        curType["subjects"][subject] = {"groups": {}}

    curSubject = curType["subjects"][subject]
    if not group in curSubject["groups"]:
        curSubject["groups"][group] = {"subGroups" : [] }

    curGroup = curSubject["groups"][group]
    if not subGroup in curGroup["subGroups"]:
        curGroup["subGroups"].append(subGroup)


def schedule2location(schedule):
    return iterThrow(schedule, updLocation)
