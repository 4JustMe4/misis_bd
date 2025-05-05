from formatted_logger import getFormattedLogger
from mongo import loadJsonFromMongo
from redis_utils import loadJsonFromRedis, updateRedis
from update import update

ApiLog = getFormattedLogger("apiLog")

# sample:
# loadJson('schedule') -> dict
# loadJson('aboba') -> None
def loadJson(name):
    ApiLog.info("Load json was called")
    result = loadJsonFromRedis(name)
    if not result:
        result = loadJsonFromMongo(name)
        updateRedis(name, result)
    return result


def updateSchedule():
    ApiLog.info("Update Schedule was called")
    update()
