import os

from dotenv import load_dotenv
from pymongo import MongoClient

def get_mongodb_client():
    mongodb_client = None
    try:
        load_dotenv()
        db_user = os.getenv('MONGODB_USER', None)
        db_password = os.getenv('MONGODB_PASSWORD', None)
        db_host = os.getenv('MONGODB_HOST', None)
        db_port = os.getenv('MONGODB_PORT', None)
        db_name = os.getenv('MONGODB_DBNAME', None)

        if None not in (db_user, db_password, db_host, db_port, db_name):
            mongodb_dsn = f"mongodb://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            mongodb_client = MongoClient(mongodb_dsn)
    except Exception as ex:
        print("[EX] get_mongodb_client : ", str(ex.args))

    return mongodb_client
