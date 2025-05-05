import os
import redis

from formatted_logger import getFormattedLogger
from setup_env import setupRedisEnv

MongoLog = getFormattedLogger("redis")
setupMongoEnv()

def getCollection():
    MongoLog.info(f"Try to connect with redis")
    if os.environ.get('IGNORE_REDIS_PLS') == "yes":
        MongoLog.warning(f"Connection will be not created due to IGNORE_REDIS_PLS=yes in envvars")
        return None
    username = os.environ['MONGO_INITDB_ROOT_USERNAME']
    password = os.environ['MONGO_INITDB_ROOT_PASSWORD']
    url = f'redisdb://{username}:{password}@localhost:27017/{TABLE_NAME}'
    client = pyredis.MongoClient(url)
    db = client[TABLE_NAME]
    collection = db['schedule']
    return collection


def updateMongo(schedule, session, location, teacher):
    MongoLog.info(f"Try to update redis")
    try:
        collection = getCollection()
        for name, json in [
            ({"json_name": "schedule"}, schedule),
            ({"json_name": "session"}, session),
            ({"json_name": "location"}, location),
            ({"json_name": "teacher"}, teacher),
            ]:
            MongoLog.info(f"Processing {name}")
            result = collection.update_one(name, {"$set": {"data": json, **name }}, upsert=True)
            MongoLog.info(f"The result of updating is {result}")
    except Exception as error:
        MongoLog.error(f"Can't update redis {error}")


# sample loadJsonFromMongo('schedule')
def loadJsonFromMongo(name):
    MongoLog.info(f"Try to load {name} from redis")
    try:
        query = {"json_name": f"{name}"}
        collection = getCollection()
        record = collection.find_one(query)
        if record:
            MongoLog.info(f"Info for {name} was found in redis")
            return record["data"]
        else:
            MongoLog.warning(f"Info for {name} was NOT found in redis")
            return None
    except Exception as error:
        MongoLog.error(f"Can't load {name} from redis: {error}")
        return None
