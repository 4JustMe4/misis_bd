import logging

from url2schedule import url2schedule
from schedule2location import schedule2location
from schedule2teacher import schedule2teacher
from get_urls import getNewUrl

Log = logging.Logger("updater")

if __name__ == "__main__":
    Log.info('Start json updating')
    schedule = {}
    for url in getNewUrl():
        if url.endswith('.xlsx'):
            Log.warning(f'Ignore .xlxs: {url}')
            continue
        schedule |= url2schedule(url)

    with open('group.json', 'w') as f:
        json.dump(schedule, f, indent=2, ensure_ascii=False, sort_keys=True)

    byLocation = schedule2location(schedule)
    with open('location.json', 'w') as f:
        json.dump(byLocation, f, indent=2, ensure_ascii=False, sort_keys=True)

    byTeacher = schedule2teacher(schedule)
    with open('teacher.json', 'w') as f:
        json.dump(byTeacher, f, indent=2, ensure_ascii=False, sort_keys=True)
