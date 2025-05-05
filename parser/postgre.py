import logging
import psycopg

from datetime import datetime

PostgreLog = logging.Logger("postgre")
TABLE_NAME = "files"

def createIfNeed(cursor):
    PostgreLog.warning(f"Check if table {TABLE_NAME} exists")
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            url TEXT PRIMARY KEY,
            data BYTEA NOT NULL,
            createdAt TIMESTAMP
        );
    """)

def getData(cursor, url):
    PostgreLog.warning(f"Fetch data for url from postgre: {url}")
    cursor.execute('SELECT data, createdAt FROM files WHERE url = %s;', (url, ))
    result = cursor.fetchone()
    if result:
        PostgreLog.warning(f"Data sucsessfuly fetched")
        return result[0]
    else:
        PostgreLog.warning(f"Data not found")
        return ''


def insertData(cursor, url, data):
    PostgreLog.warning(f"Add data for url to postgre: {url}")
    cursor.execute('''
        INSERT INTO files (url, data, createdAt) 
        VALUES (%s, %s, %s);
        ''',
        (url, data, datetime.now())
    )


def getConnection():
    PostgreLog.warning(f"Try connect to postgre")
    connection = psycopg.connect(
        dbname="db",
        user="bot",
        password="12345678",
    )
    return connection


def loadUrlFromPostgre(url):
    PostgreLog.warning(f"Try to load url {url} from postgre")
    try:
        connection = getConnection()
        cursor = connection.cursor()
        createIfNeed(cursor)
        data = getData(cursor, url)
        connection.commit()
        return data
    except Exception as error:
        PostgreLog.error(f"Can't connect to postgre {error}")
        return ''


def insertUrlToPostgre(url, data):
    PostgreLog.error(f"Try to add url {url} to postgre")
    try:
        connection = getConnection()
        cursor = connection.cursor()
        insertData(cursor, url, data)
        connection.commit()
        return data
    except Exception as error:
        PostgreLog.error(f"Can't connect to postgre {error}")
        return ''