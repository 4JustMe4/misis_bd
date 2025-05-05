from formatted_logger import getFormattedLogger
from utils import processUrl

DAYS = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
DAY_WIDTH = 14
Url2scheduleLog = getFormattedLogger("url2schedule")


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
            Url2scheduleLog.warning(f"Bad day. Sheet: {sheet.name}, Group: {groupName}-{subGroupName}. Expected {day} at (0, {dayStart}), recieved {dayName}")
            continue

        dayWidth = getDayWidth(sheet, dayStart, dayName)
        if dayWidth != DAY_WIDTH:
            Url2scheduleLog.warning(f"Bad day line. Sheet: {sheet.name}, Group: {groupName}-{subGroupName}, Day: {dayName}. Expected {DAY_WIDTH} line, recieved {dayWidth}")
            continue

        subGroup[day] = parseDay(sheet, groupName, subGroupName, dayName, dayStart, subGroupStart)
        dayStart += dayWidth

    return subGroup


def parseGroup(sheet, groupName, groupStart, width):
    Url2scheduleLog.debug(f'Process sheet {sheet.name}, group {groupName}')
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
            Url2scheduleLog.error(f"Bad sheet {sheet.name}. Expected {value} in {idx}")
            return None
    
    schedule = {}
    maxGroupStart = len(sheet.row(0))
    groupStart = 3
    while groupStart < maxGroupStart:
        groupWidth = getGroupWidth(sheet, groupStart)
        groupName = sheet.cell_value(0, groupStart)
        if not groupName:
            Url2scheduleLog.warning(f"Bad column. Sheet: {sheet.name}. Expected group number at (0, {groupStart}), recieved {groupName}")
            continue

        schedule[groupName] = parseGroup(sheet, groupName, groupStart, groupWidth)
        groupStart += groupWidth

    return schedule


def url2schedule(url):
    return processUrl(url, parseSheet)
