import logging
import requests
import xlrd

from formatted_logger import getFormattedLogger
from postgre import loadUrlFromPostgre, insertUrlToPostgre

UtilsLog = getFormattedLogger("utils")


def processFile(file, sheetFunc):
    UtilsLog.warning(f"Process file {file}")
    workbook = xlrd.open_workbook(file)
    result = {}
    for sheet_index in range(workbook.nsheets):
        sheet = workbook.sheet_by_index(sheet_index)
        UtilsLog.warning(F"Parsing shedule from {sheet.name}")
        new_result = sheetFunc(sheet)
        if new_result:
            result |= new_result
        else:
            UtilsLog.warning(f"Can't parse shedule from {sheet.name}")
    return result


def loadUrl(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        UtilsLog.error(f"Can't dowload file with url {url}. Status code: {response.status_code}")
        return ''


def processUrl(url, sheetFunc):
    UtilsLog.warning(f"Process url {url}")
    data = loadUrlFromPostgre(url)
    if not data:
        data = loadUrl(url)
        insertUrlToPostgre(url, data)
    if data:
        filename = 'tmp.xls'
        with open(filename, 'wb') as f:
            f.write(data)
        result = processFile(filename, sheetFunc)
    else:
        UtilsLog.error(f"Can't dowload data from anywhere")
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
