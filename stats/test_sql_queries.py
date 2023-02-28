import mysql.connector as mysql
import environ

env = environ.Env()
environ.Env.read_env(overwrite=True)  # reading .env file

#HOST = "server42.areait.lv" # or "domain.com"
HOST = "localhost" # or "domain.com"

# database name, if you want just to connect to MySQL server, leave it empty
DATABASE = env.str('MYSQL_DB_NAME')
#DATABASE = "stats_local"

# Ensure that different user credentials are used if connecting locally vs hosted.
HOSTED = env.str('HOSTED')
print('HOSTED:',HOSTED)
if not HOSTED:
    USER = env.str('MYSQL_HOSTED_DEV_DB_USER')
    PASSWORD = env.str('MYSQL_HOSTED_DEV_PWD')
else:
    USER = env.str('MYSQL_DB_USER')
    PASSWORD = env.str('MYSQL_PWD')

# connect to MySQL server
print('HOST:',HOST)
print('DATABASE:',DATABASE)
print('USER:',USER)
print('PASSWORD:',PASSWORD)
db_connection = mysql.connect(host=HOST, database=DATABASE, user=USER, password=PASSWORD)
print("Connected to:", db_connection.get_server_info())

