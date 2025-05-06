import os

from .formatted_logger import getFormattedLogger


EnvLog = getFormattedLogger("setupEnv")

def setupPostgreEnv():
    EnvLog.info('Set up envvars for postgre')
    if os.environ.get('POSTGRES_PASSWORD') is None:
        EnvLog.warning('Use hardcoded values. IT IS ERROR IF YOU SEE IT ON SERVER')

        os.environ['POSTGRES_USER'] = 'bot'
        os.environ['POSTGRES_PASSWORD'] = '12345678'
        os.environ['POSTGRES_DB'] = 'db'
        os.environ['BOT_POSTGRES_PORT'] = '5432'
        os.environ['BOT_POSTGRES_HOSTNAME'] = 'localhost'
    else:
        EnvLog.info('Use preset env for postgre')

def setupMongoEnv():
    EnvLog.info('Set up envvars for mongo')
    if os.environ.get('MONGO_INITDB_ROOT_USERNAME') is None:
        EnvLog.warning('Use hardcoded values. IT IS ERROR IF YOU SEE IT ON SERVER')

        os.environ['MONGO_INITDB_ROOT_USERNAME'] = 'bot'
        os.environ['MONGO_INITDB_ROOT_PASSWORD'] = '12345678'
        os.environ['MONGO_INITDB_DATABASE'] = 'schedule'
        os.environ['BOT_MONGO_PORT'] = '27017'
        os.environ['BOT_MONGO_HOSTNAME'] = 'localhost'
    else:
        EnvLog.info('Use preset env for mongo')

def setupRedisEnv():
    EnvLog.info('Set up envvars for redis')
    if os.environ.get('BOT_REDIS_HOSTNAME') is None:
        EnvLog.warning('Use hardcoded values. IT IS ERROR IF YOU SEE IT ON SERVER')

        os.environ['BOT_REDIS_PORT'] = '6379'
        os.environ['BOT_REDIS_HOSTNAME'] = 'localhost'
        os.environ['REDIS_PASSWORD'] = '12345678'
    else:
        EnvLog.info('Use preset env for redis')
