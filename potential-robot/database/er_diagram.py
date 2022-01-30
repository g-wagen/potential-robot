# import os
# import dotenv
# import sqlalchemy
# import sqlalchemy_schemadisplay

# # Load environment variables from the .env file
# dotenv.load_dotenv()

# wh_cred = {
#     'user': os.environ['WAREHOUSE_USER'],
#     'pw': os.environ['WAREHOUSE_USER_PW'],
#     'host': os.environ['WAREHOUSE_HOST'],
#     'port': os.environ['WAREHOUSE_PORT_EXTERN'],
# }



# db_type = 'mysql+mysqlconnector'
# db = 'recipes'

# # create the pydot graph object by autoloading all tables via a bound metadata object
# graph = sqlalchemy_schemadisplay.create_schema_graph(metadata=sqlalchemy.MetaData(
#     f"{db_type}://{wh_cred['user']}:{wh_cred['pw']}@{wh_cred['host']}:{wh_cred['port']}/{db}"),
#     show_datatypes=False, # The image would get nasty big if we'd show the datatypes
#     show_indexes=False, # ditto for indexes
#     rankdir='LR', # From left to right (instead of top to bottom)
#     concentrate=False # Don't try to join the relation lines together
# )
# graph.write_png('dbschema.png') # write out the file