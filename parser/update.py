import logging

from url2schedule import iterThrow, updLocation, updTeacher, downloadFile
from get_urls import getNewUrl

Log = logging.Logger("Updater")

if __name__ == "__main__":
    Log.info('Start json updating')
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