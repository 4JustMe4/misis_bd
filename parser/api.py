from formatted_logger import getFormattedLogger
from mongo import loadJsonFromMongo
from update import update

ApiLog = getFormattedLogger("apiLog")

# sample:
# loadJson('schedule') -> dict
# loadJson('aboba') -> None
def loadJson(name):
    ApiLog.info("Load json was called")
    return loadJsonFromMongo(name)

def updateSchedule():
    ApiLog.info("Update Schedule was called")
    update()
