from utils import iterThrow


def updTeacher(byTeacher, group, subGroup, day, lesson, type, location, subject):
    if not '\n' in subject:
        return
    splited = subject.rsplit('\n', maxsplit=3)
    if len(splited) < 2:
        return
    teacher = splited[1]
    if teacher == "":
        return
    if not teacher in byTeacher:
        byTeacher[teacher] = {}

    curTeacher = byTeacher[teacher]
    if not day in curTeacher:
        curTeacher[day] = {}

    curDay = curTeacher[day]
    if not lesson in curDay:
        curDay[lesson] = {}

    curLesson = curDay[lesson]
    if not type in curLesson:
        curLesson[type] = { "subjects": {}}

    curType = curLesson[type]
    if not subject in curType["subjects"]:
        curType["subjects"][subject] = {"groups": {}, "locations": []}

    curSubject = curType["subjects"][subject]
    if not group in curSubject["groups"]:
        curSubject["groups"][group] = {"subGroups" : [] }

    curGroup = curSubject["groups"][group]
    if not subGroup in curGroup["subGroups"]:
        curGroup["subGroups"].append(subGroup)

    if location not in curSubject["locations"]:
        curSubject["locations"].append(location)


def schedule2teacher(schedule):
    return iterThrow(schedule, updTeacher)
