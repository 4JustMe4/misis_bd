import requests
import os
import xlrd
import logging
import json

from get_urls import getNewUrl

DAYS = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
DAY_WIDTH = 14

Log = logging.Logger("parser")


def getGroupWidth(sheet, startIdx):
    idx = startIdx + 1
    maxIdx = len(sheet.row(0))
    while idx < maxIdx and sheet.cell_value(0, idx) == "":
        idx += 1
    return idx - startIdx


def getDayWidth(sheet, startIdx, dayName):
    idx = startIdx + 1
    maxIdx = sheet.nrows
    while idx < maxIdx and sheet.cell_value(idx, 0) == "":
        idx += 1

    if dayName == DAYS[-1]:
        idx += 1
    return idx - startIdx


def parseLesson(sheet, dayName, lessonStart, subGroupStart):
    forceIgnore = False
    if dayName == DAYS[-1] and lessonStart + 1 == sheet.nrows:
        forceIgnore = True

    lesson = {
        "upper": {
            "subject": sheet.cell_value(lessonStart, subGroupStart),
            "place": sheet.cell_value(lessonStart, subGroupStart + 1),
        },
        "lower": {
            "subject": "" if forceIgnore else sheet.cell_value(lessonStart + 1, subGroupStart),
            "place": "" if forceIgnore else sheet.cell_value(lessonStart + 1, subGroupStart + 1),
        },
    }
    return lesson


def parseDay(sheet, groupName, subGroupName, dayName, dayStart, subGroupStart):
    day = {}
    for lesson in range(0, DAY_WIDTH, 2):
        day[str(lesson // 2 + 1)] = parseLesson(sheet, dayName, dayStart + lesson, subGroupStart)

    return day


def parseSubGroup(sheet, groupName, subGroupName, subGroupStart):
    subGroup = {}
    dayStart = 2
    for day in DAYS:
        dayName = sheet.cell_value(dayStart, 0)
        if day != dayName:
            Log.warning(f"Bad day. Sheet: {sheet.name}, Group: {groupName}-{subGroupName}. Expected {day} at (0, {dayStart}), recieved {dayName}")
            continue

        dayWidth = getDayWidth(sheet, dayStart, dayName)
        if dayWidth != DAY_WIDTH:
            Log.warning(f"Bad day line. Sheet: {sheet.name}, Group: {groupName}-{subGroupName}, Day: {dayName}. Expected {DAY_WIDTH} line, recieved {dayWidth}")
            continue

        subGroup[day] = parseDay(sheet, groupName, subGroupName, dayName, dayStart, subGroupStart)
        dayStart += dayWidth

    return subGroup


def parseGroup(sheet, groupName, groupStart, width):
    Log.info(f'Process sheet {sheet.name}, group {groupName}')
    group = {}
    for subGroup in range(0, width, 2):
        group[str(subGroup // 2 + 1)] = parseSubGroup(sheet, groupName, subGroup, groupStart + subGroup)
    return group


def parseSheet(sheet):
    # TODO: support maga in gi
    head_cells = {
        (0, 0): 'Дата',
        (0, 1): 'Номер',
        (0, 2): 'Время',
    }
    for idx, value in head_cells.items():
        if sheet.cell_value(idx[0], idx[1]) != value:
            Log.error(f"Bad sheet {sheet.name}. Expected {value} in {idx}")
            return None
    
    schedule = {}
    maxGroupStart = len(sheet.row(0))
    groupStart = 3
    while groupStart < maxGroupStart:
        groupWidth = getGroupWidth(sheet, groupStart)
        groupName = sheet.cell_value(0, groupStart)
        if not groupName:
            Log.warning(f"Bad column. Sheet: {sheet.name}. Expected group number at (0, {groupStart}), recieved {groupName}")
            continue

        schedule[groupName] = parseGroup(sheet, groupName, groupStart, groupWidth)
        groupStart += groupWidth

    return schedule
            

def downloadFile(url):
    Log.warning(f"Process url {url}")
    response = requests.get(url)
    if response.status_code == 200:
        filename = 'tmp.xls'
        with open('tmp.xls', 'wb') as f:
            f.write(response.content)

        workbook = xlrd.open_workbook(filename)
        schedule = {}
        for sheet_index in range(workbook.nsheets):
            sheet = workbook.sheet_by_index(sheet_index)
            Log.info(F"Parsing shedule from {sheet.name}")
            new_schedule = parseSheet(sheet)
            if new_schedule:
                schedule |= new_schedule
            else:
                Log.warning(f"Can't parse shedule from {sheet.name}")

        # if 'ББИ-24-1' in schedule:
        #     print(json.dumps(schedule["ББИ-24-1"]["1"], indent=2, ensure_ascii=False))

    else:
        Log.error(f"Не удалось скачать файл. Код статуса: {response.status_code}")

    return schedule


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


if __name__ == "__main__":
    schedule = {}
    for url in getNewUrl():
        if url.endswith('.xlsx'):
            Log.warning(f'Ignore .xlxs: {url}')
            continue
        schedule |= downloadFile(url)

    with open('group.json', 'w') as f:
        json.dump(schedule, f, indent=2, ensure_ascii=False, sort_keys=True)

    byLocation = iterThrow(schedule, updLocation)
    with open('location.json', 'w') as f:
        json.dump(byLocation, f, indent=2, ensure_ascii=False, sort_keys=True)

    byTeacher = iterThrow(schedule, updTeacher)
    with open('teacher.json', 'w') as f:
        json.dump(byTeacher, f, indent=2, ensure_ascii=False, sort_keys=True)
