import os
import dotenv
import sqlalchemy

# Load environment variables from the .env file
dotenv.load_dotenv()


lake_db_credentials = {
    'user': os.environ['LAKE_USER'],
    'pw': os.environ['LAKE_USER_PW'],
    'host': os.environ['LAKE_HOST'],
    'port': os.environ['LAKE_PORT_EXTERN']
}

warehouse_db_credentials = {
    'user': os.environ['WAREHOUSE_USER'],
    'pw': os.environ['WAREHOUSE_USER_PW'],
    'host': os.environ['WAREHOUSE_HOST'],
    'port': os.environ['WAREHOUSE_PORT_EXTERN'],
}


def connect_to_db(db_type, user, pw, host, port, db):
    """General function to connect to SQL databases"""
    db_engine = sqlalchemy.create_engine(
        f'{db_type}://{user}:{pw}@{host}:{port}/{db}')
    db_connection = db_engine.connect()
    return db_connection


def connect_to_recipes():
    """Connect to the recipe database on the warehouse server"""
    db_type = 'mysql+mysqlconnector'
    db = os.environ['RECIPE_DB']
    return connect_to_db(db_type, *warehouse_db_credentials.values(), db)


def connect_to_datalake():
    """Connect to my very cold and wet Data Lake"""
    db_type = 'mysql+mysqlconnector'
    db = os.environ['LAKE_NAME']
    return connect_to_db(db_type, *lake_db_credentials.values(), db)


def connect_to_datawarehouse():
    """Connect to my incredibly dry and dusty Data Warehouse"""
    db_type = 'mysql+mysqlconnector'
    db = os.environ['WAREHOUSE_NAME']
    return connect_to_db(db_type, *warehouse_db_credentials.values(), db)