import logging
import requests
import xlrd


UtilsLog = logging.Logger("utils")


def processFile(file, sheetFunc):
    UtilsLog.warning(f"Process file {file}")
    workbook = xlrd.open_workbook(file)
    result = {}
    for sheet_index in range(workbook.nsheets):
        sheet = workbook.sheet_by_index(sheet_index)
        UtilsLog.info(F"Parsing shedule from {sheet.name}")
        new_result = sheetFunc(sheet)
        if new_schedule:
            result |= new_result
        else:
            UtilsLog.warning(f"Can't parse shedule from {sheet.name}")


def processUrl(url, sheetFunc):
    UtilsLog.warning(f"Process url {url}")
    response = requests.get(url)
    if response.status_code == 200:
        filename = 'tmp.xls'
        with open(filename, 'wb') as f:
            f.write(response.content)
        result = processFile(filename, sheetFunc)
    else:
        UtilsLog.error(f"Can't dowload file with url {url}. Statuc code: {response.status_code}")

    return result


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
