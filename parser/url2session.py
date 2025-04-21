import logging

from utils import processFile

DAY_WIDTH = 2
Url2sessionLog = logging.Logger("url2session")


def getGroupWidth(sheet, startIdx):
    idx = startIdx + 1
    maxIdx = len(sheet.row(0))
    while idx < maxIdx and sheet.cell_value(0, idx) == "":
        idx += 1
    return idx - startIdx


def getDayWidth(sheet, startIdx):
    idx = startIdx + 1
    maxIdx = sheet.nrows
    while idx < maxIdx and sheet.cell_value(idx, 0) == "":
        idx += 1

    return idx - startIdx


def parseExam(sheet, date, examStart, subGroupStart):
    # forceIgnore = False
    # if examStart + 1 == sheet.nrows:
    #     forceIgnore = True

    exam = {
        "subject": sheet.cell_value(examStart, subGroupStart),
        "place": sheet.cell_value(examStart, subGroupStart + 1),
    }
    return exam


def parseDay(sheet, groupName, subGroupName, date, dayStart, subGroupStart):
    day = {}
    for exam in range(0, DAY_WIDTH):
        day[exam + 1] = parseExam(sheet, date, dayStart + exam, subGroupStart)

    return day


def verifyDate(date):
    dotsPos = {2, 5}
    for i in range(len(date)):
        if i in dotsPos:
            if date[i] != '.':
                return False
        else:
            if date[i] < '0' or '9' < date[i]:
                return False
    return True


def parseSubGroup(sheet, groupName, subGroupName, subGroupStart):
    subGroup = {}
    for dayStart in range(2, sheet.nrows, DAY_WIDTH):
        date = sheet.cell_value(dayStart, 0).split('\n')[0]
        if not verifyDate(date):
            Url2sessionLog.warning(f"Bad day. Sheet: {sheet.name}, Group: {groupName}-{subGroupName}. Expected dateline object at (0, {dayStart}), recieved {date}")
            continue

        dayWidth = getDayWidth(sheet, dayStart)
        if dayWidth != DAY_WIDTH:
            Url2sessionLog.warning(f"Bad day line. Sheet: {sheet.name}, Group: {groupName}-{subGroupName}, date: {date}. Expected {DAY_WIDTH} line, recieved {dayWidth}")
            continue

        subGroup[date] = parseDay(sheet, groupName, subGroupName, date, dayStart, subGroupStart)

    return subGroup


def parseGroup(sheet, groupName, groupStart, width):
    Url2sessionLog.info(f'Process sheet {sheet.name}, group {groupName}')
    group = {}
    for subGroup in range(0, width, 2):
        group[str(subGroup // 2 + 1)] = parseSubGroup(sheet, groupName, subGroup, groupStart + subGroup)
    return group


def parseSheet(sheet):
    head_cells = {
        (0, 0): 'Дата',
        (0, 1): 'Номер',
        (0, 2): 'Время',
    }
    for idx, value in head_cells.items():
        if sheet.cell_value(idx[0], idx[1]) != value:
            Url2sessionLog.error(f"Bad sheet {sheet.name}. Expected {value} in {idx}")
            return None
    
    session = {}
    maxGroupStart = len(sheet.row(0))
    groupStart = 3
    while groupStart < maxGroupStart:
        groupWidth = getGroupWidth(sheet, groupStart)
        groupName = sheet.cell_value(0, groupStart)
        if not groupName:
            Url2sessionLog.warning(f"Bad column. Sheet: {sheet.name}. Expected group number at (0, {groupStart}), recieved {groupName}")
            continue

        session[groupName] = parseGroup(sheet, groupName, groupStart, groupWidth)
        groupStart += groupWidth

    return session


def url2session(url):
    return processFile(url, parseSheet)
