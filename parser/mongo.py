import os
import pymongo

from .formatted_logger import getFormattedLogger
from .setup_env import setupMongoEnv

MongoLog = getFormattedLogger("mongo")
setupMongoEnv()

def getCollection(name):
    MongoLog.info(f"Try to connect with monga")
    if os.environ.get('IGNORE_MONGO_PLS') == "yes":
        MongoLog.warning(f"Connection will be not created due to IGNORE_MONGO_PLS=yes in envvars")
        return None
    username = os.environ['MONGO_INITDB_ROOT_USERNAME']
    password = os.environ['MONGO_INITDB_ROOT_PASSWORD']
    dbname = os.environ['MONGO_INITDB_DATABASE']
    port = os.environ['BOT_MONGO_PORT']
    host = os.environ['BOT_MONGO_HOSTNAME']
    url = f'mongodb://{username}:{password}@{host}:{port}/'
    client = pymongo.MongoClient(url)
    db = client[dbname]
    collection = db[name]
    return collection


def updateMongo(schedule, session, location, teacher):
    MongoLog.info(f"Try to update monga")
    try:
        for name, json in [
            ({"json_name": "schedule"}, schedule),
            ({"json_name": "session"}, session),
            ({"json_name": "location"}, location),
            ({"json_name": "teacher"}, teacher),
            ]:
            collection = getCollection(name["json_name"])
            MongoLog.info(f"Processing {name}")
            result = collection.update_one(name, {"$set": {"data": json, **name }}, upsert=True)
            MongoLog.info(f"The result of updating is {result}")
    except Exception as error:
        MongoLog.error(f"Can't update mongo {error}")


# sample loadJsonFromMongo('schedule')
def loadJsonFromMongo(name):
    MongoLog.info(f"Try to load {name} from mongo")
    try:
        query = {"json_name": f"{name}"}
        collection = getCollection(name)
        record = collection.find_one(query)
        if record:
            MongoLog.info(f"Info for {name} was found in mongo")
            return record["data"]
        else:
            MongoLog.warning(f"Info for {name} was NOT found in mongo")
            return None
    except Exception as error:
        MongoLog.error(f"Can't load {name} from mongo: {error}")
        return None
