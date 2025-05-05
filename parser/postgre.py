import psycopg
import os

from datetime import datetime
from formatted_logger import getFormattedLogger
from setup_env import setupPostgreEnv

PostgreLog = getFormattedLogger("postgre")
TABLE_NAME = "files"
setupPostgreEnv()

def createIfNeed(cursor):
    PostgreLog.info(f"Check if table {TABLE_NAME} exists")
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            url TEXT PRIMARY KEY,
            data BYTEA NOT NULL,
            createdAt TIMESTAMP
        );
    """)


def getData(cursor, url):
    PostgreLog.info(f"Try to fetch data for url from postgre: {url}")
    cursor.execute('SELECT data, createdAt FROM files WHERE url = %s;', (url, ))
    result = cursor.fetchone()
    if result:
        PostgreLog.info(f"Data sucsessfuly fetched")
        return result[0]
    else:
        PostgreLog.warning(f"Data not found")
        return ''


def insertData(cursor, url, data):
    PostgreLog.info(f"Add data for url to postgre: {url}")
    cursor.execute('''
        INSERT INTO files (url, data, createdAt) 
        VALUES (%s, %s, %s);
        ''',
        (url, data, datetime.now())
    )


def getConnection():
    PostgreLog.info(f"Try connect to postgre")
    connection = psycopg.connect(
        dbname=os.environ['POSTGRES_DB'],
        user=os.environ['POSTGRES_USER'],
        password=os.environ['POSTGRES_PASSWORD'],
        port=os.environ['BOT_POSTGRES_PORT'],
        host=os.environ['BOT_POSTGRES_HOSTNAME'],
    )
    return connection


def loadUrlFromPostgre(url):
    PostgreLog.info(f"Try to load url {url} from postgre")
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
    PostgreLog.info(f"Try to add url {url} to postgre")
    try:
        connection = getConnection()
        cursor = connection.cursor()
        insertData(cursor, url, data)
        connection.commit()
        return data
    except Exception as error:
        PostgreLog.error(f"Can't connect to postgre {error}")
        return ''