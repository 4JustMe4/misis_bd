import os
import pymongo

from formatted_logger import getFormattedLogger
from setup_env import setupMongoEnv

MongoLog = getFormattedLogger("mongo")
TABLE_NAME = 'schedule'
setupMongoEnv()

def getCollection():
    MongoLog.info(f"Try to connect with monga")
    if os.environ.get('IGNORE_MONGO_PLS') == "yes":
        MongoLog.warning(f"Connection will be not created due to IGNORE_MONGO_PLS=yes in envvars")
        return None
    username = os.environ['MONGO_INITDB_ROOT_USERNAME']
    password = os.environ['MONGO_INITDB_ROOT_PASSWORD']
    url = f'mongodb://{username}:{password}@localhost:27017/{TABLE_NAME}'
    client = pymongo.MongoClient(url)
    db = client[TABLE_NAME]
    collection = db['schedule']
    return collection


def updateMongo(schedule, session, location, teacher):
    MongoLog.info(f"Try to update monga")
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
        MongoLog.error(f"Can't update mongo {error}")


# sample loadJsonFromMongo('schedule')
def loadJsonFromMongo(name):
    MongoLog.info(f"Try to load {name} from mongo")
    try:
        query = {"json_name": f"{name}"}
        collection = getCollection()
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
