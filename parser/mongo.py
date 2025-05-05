import pymongo

from formatted_logger import getFormattedLogger

MongoLog = getFormattedLogger("mongo")
TABLE_NAME = 'schedule'

def updateMongo(schedule, session, location, teacher):
    MongoLog.info(f"Try to connect with monga")
    try:
        client = pymongo.MongoClient('mongodb://localhost:27017/')
        db = client[TABLE_NAME]
        collection = db['schedule']

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
        MongoLog.error(f"Can't connect to db {error}")
