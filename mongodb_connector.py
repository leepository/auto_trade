import os

from dotenv import load_dotenv
from pymongo import MongoClient

def get_mongodb_client():
    mongodb_client = None
    try:
        load_dotenv()
        app_env = os.getenv('APP_ENV', 'DEV')

        dev_db_user = os.getenv('DEV_MONGODB_USER', None)
        dev_db_password = os.getenv('DEV_MONGODB_PASSWORD', None)
        dev_db_host = os.getenv('DEV_MONGODB_HOST', None)

        product_db_user = os.getenv('PRODUCT_MONGODB_USER', None)
        product_db_password = os.getenv('PRODUCT_MONGODB_PASSWORD', None)
        product_db_host = os.getenv('PRODUCT_MONGODB_HOST', None)

        db_port = os.getenv('MONGODB_PORT', None)
        db_name = os.getenv('MONGODB_DBNAME', None)
        db_options = os.getenv('MONGODB_OPTIONS', None)

        if app_env == 'DEV':
            print("#1")
            if None not in (dev_db_user, dev_db_password, dev_db_host, db_port, db_name, db_options):
                mongodb_dsn = f"mongodb://{dev_db_user}:{dev_db_password}@{dev_db_host}:{db_port}/{db_name}"
        else:
            if None not in (product_db_user, product_db_password, product_db_host, db_port, db_name, db_options):
                mongodb_dsn = f"mongodb://{product_db_user}:{product_db_password}@{product_db_host}:{db_port}/?{db_options}"
        mongodb_client = MongoClient(mongodb_dsn)
    except Exception as ex:
        print("[EX] get_mongodb_client : ", str(ex.args))

    return mongodb_client
