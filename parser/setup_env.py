import os

from formatted_logger import getFormattedLogger


EnvLog = getFormattedLogger("SetupEnv")

def setupPostgreEnv():
    EnvLog.info('Set up envvars for postgre')
    if os.environ.get('POSTGRES_PASSWORD') is None:
        EnvLog.warning('Use hardcoded values. IT IS ERROR IF YOU SEE IT ON SERVER')

        os.environ['POSTGRES_USER'] = 'bot'
        os.environ['POSTGRES_PASSWORD'] = '12345678'
        os.environ['POSTGRES_DB'] = 'db'
    else:
        EnvLog.info('Use preset env for postgre')

def setupMongoEnv():
    EnvLog.info('Set up envvars for mongo')
    if os.environ.get('MONGO_INITDB_ROOT_USERNAME') is None:
        EnvLog.warning('Use hardcoded values. IT IS ERROR IF YOU SEE IT ON SERVER')
        os.environ['MONGO_INITDB_ROOT_USERNAME'] = 'bot'
        os.environ['MONGO_INITDB_ROOT_PASSWORD'] = '12345678'
    else:
        EnvLog.info('Use preset env for mongo')

def setupRedisEnv():
    EnvLog.info('Set up envvars for redis')
    if os.environ.get('BOT_REDIS_HOSTNAME') is None:
        EnvLog.warning('Use hardcoded values. IT IS ERROR IF YOU SEE IT ON SERVER')
