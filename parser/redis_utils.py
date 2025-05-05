import os
import redis

from formatted_logger import getFormattedLogger
from setup_env import setupRedisEnv

RedisLog = getFormattedLogger("redis")
setupRedisEnv()

def getClient():
    RedisLog.info(f"Try to connect with redis")
    if os.environ.get('IGNORE_REDIS_PLS') == "yes":
        RedisLog.warning(f"Connection will be not created due to IGNORE_REDIS_PLS=yes in envvars")
        return None
    host = os.environ['BOT_REDIS_HOSTNAME']
    port = os.environ['BOT_REDIS_PORT']
    password = os.environ['REDIS_PASSWORD']
    client = redis.Redis(host=host, port=int(port), password=password, decode_responses=True)
    return client


def updateRedis(name, data):
    RedisLog.info(f"Try to update redis for name {name}")
    try:
        client = getClient()
        result = client.json().set(name, ".", data)
        RedisLog.info(f"The result of updating is {result}")
    except Exception as error:
        RedisLog.error(f"Can't update redis {error}")


def updateAllRedis(schedule, session, location, teacher):
    RedisLog.info(f"Try to update all redis records")
    updateRedis("schedule", schedule)
    updateRedis("location", location)
    updateRedis("session", session)
    updateRedis("teacher", teacher)


def loadJsonFromRedis(name):
    RedisLog.info(f"Try to load {name} from redis")
    try:
        client = getClient()
        record = client.json().get(name)
        if record:
            RedisLog.info(f"Info for {name} was found in redis")
            return record["data"]
        else:
            RedisLog.warning(f"Info for {name} was NOT found in redis")
            return None
    except Exception as error:
        RedisLog.error(f"Can't load {name} from redis: {error}")
        return None
