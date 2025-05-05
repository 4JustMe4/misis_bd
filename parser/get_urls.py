import requests

from bs4 import BeautifulSoup
from formatted_logger import getFormattedLogger

MISIS_SCHEDULE = 'https://misis.ru/students/schedule/'
MISIS_SESSION = 'https://misis.ru/students/session/'
FILES_PREFIX = 'https://misis.ru'

UrlLog = getFormattedLogger('url_updater')


def getAllLinks(url):
    UrlLog.info(f'Processing url: {url}')
    response = requests.get(url)
    links = []
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        rawLinks = [a.get('href') for a in soup.find_all('a')]
        for link in rawLinks:
            if link:
                if link.startswith('/files/-/'):
                    links.append(FILES_PREFIX + link)
                else:
                    UrlLog.debug(f'Ignore {link}')
    else:
        UrlLog.error(f'Request to {MISIS_SCHEDULE} was failed: {response.status_code}')
    UrlLog.info(f'The list of urls is: {links}')
    return links


def getNewSheduleUrls():
    UrlLog.info(f'Reupdate url lists for {MISIS_SCHEDULE}')
    return getAllLinks(MISIS_SCHEDULE)

def getNewSessionUrls():
    UrlLog.info(f'Reupdate url lists for {MISIS_SESSION}')
    return getAllLinks(MISIS_SESSION)


if __name__ == "__main__":
    print(f'Schedule: {getNewSheduleUrls()}')
    print(f'Session: {getNewSessionUrls()}')

# backuped links
# urls = [
#     'https://misis.ru/files/-/7d25c03a7104eef05c070497a0102925/140225_gi.xls',
#     'https://misis.ru/files/-/180708c8a2a7dd621a10142628cd321e/140225_ibmi.xls',
# #    'https://misis.ru/files/-/a68f9212d6db71b44115abddbfb5e71b/140225_ibo.xlsx', TODO: xls with bad format
#     'https://misis.ru/files/-/75da0398c2654e2a4a3bbba5f203935f/140225_ieu.xls',
#     'https://misis.ru/files/-/9e080c766c3e47bd62c1e0311dbad190/140225_ifki.xls',
#     'https://misis.ru/files/-/40ee7e88bcb71d176a4cd829f91b81c3/140225_ikn.xls',
#     'https://misis.ru/files/-/c57b93865ae04c54a92abf2b5335ab7e/140225_inm.xls',
#     'https://misis.ru/files/-/e5bc8211c013c17eab64e8071cce418a/140225_it.xls',
#     'https://misis.ru/files/-/8b077073a7c38f58d737451e79eb5fbd/140225_pish.xls',
# ]