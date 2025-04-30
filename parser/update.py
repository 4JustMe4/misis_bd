import json
import logging
import os

from get_urls import getNewSheduleUrls, getNewSessionUrls
from schedule2location import schedule2location
from schedule2teacher import schedule2teacher
from url2schedule import url2schedule
from url2session import url2session

from mongo import updateMongo


Log = logging.Logger("updater")


def writeJson(data, name):
    with open(name + '.json', 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)


def dumpResults(schedule, session, location, teacher):
    os.chdir('data')
    writeJson(schedule, 'group')
    writeJson(session, 'session')
    writeJson(location, 'location')
    writeJson(teacher, 'teacher')
    updateMongo(schedule, session, location, teacher)


def getSchedules():
    schedule = {}
    for url in getNewSheduleUrls():
        if url.endswith('.xlsx'):
            Log.warning(f'Ignore .xlxs: {url}')
            continue
        schedule |= url2schedule(url)

    session = {}
    for url in getNewSessionUrls():
        if url.endswith('.xlsx'):
            Log.warning(f'Ignore .xlxs: {url}')
            continue
        session |= url2session(url)

    byLocation = schedule2location(schedule)
    byTeacher = schedule2teacher(schedule)
    return schedule, session, byLocation, byTeacher


def main():
    Log.info('Start json updating')
    schedule, session, byLocation, byTeacher = getSchedules()
    dumpResults(schedule, session, byLocation, byTeacher)


if __name__ == "__main__":
    main()
