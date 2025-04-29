import logging
import psycopg
import requests
import xlrd

from datetime import datetime

UtilsLog = logging.Logger("utils")
TABLE_NAME = "files"


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

def createIfNeed(cursor):
    UtilsLog.warning(f"Check if table {TABLE_NAME} exists")
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            url TEXT PRIMARY KEY,
            data BYTEA NOT NULL,
            createdAt TIMESTAMP
        );
    """)

def getData(cursor, url):
    UtilsLog.warning(f"Fetch data for url from db: {url}")
    cursor.execute('SELECT data, createdAt FROM files WHERE url = %s;', (url, ))
    result = cursor.fetchone()
    if result:
        UtilsLog.warning(f"Data sucsessfuly fetched")
        return result[0]
    else:
        UtilsLog.warning(f"Data not found")
        return ''


def insertData(cursor, url, data):
    UtilsLog.warning(f"Add data for url to db: {url}")
    cursor.execute('''
        INSERT INTO files (url, data, createdAt) 
        VALUES (%s, %s, %s);
        ''',
        (url, data, datetime.now())
    )

def getConnection():
    UtilsLog.warning(f"Try connect to db")
    connection = psycopg.connect(
        dbname="db",
        user="bot",
        password="12345678",
    )
    return connection


def loadUrlFromDb(url):
    UtilsLog.warning(f"Try to load url {url} from db")
    try:
        connection = getConnection()
        cursor = connection.cursor()
        createIfNeed(cursor)
        data = getData(cursor, url)
        connection.commit()
        return data
    except Exception as error:
        UtilsLog.warning(f"Can't connect to db {error}")
        return ''


def insertUrlToDb(url, data):
    UtilsLog.error(f"Try to add url {url} to db")
    try:
        connection = getConnection()
        cursor = connection.cursor()
        insertData(cursor, url, data)
        connection.commit()
        return data
    except Exception as error:
        UtilsLog.warning(f"Can't connect to db {error}")
        return ''


def processUrl(url, sheetFunc):
    UtilsLog.warning(f"Process url {url}")
    data = loadUrlFromDb(url)
    if not data:
        data = loadUrl(url)
        insertUrlToDb(url, data)
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
