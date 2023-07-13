import psycopg2
# import paramiko
import pandas as pd
# from paramiko import SSHClient
from sshtunnel import SSHTunnelForwarder
# from os.path import expanduser

import sys
from pathlib import Path

sys.path.append( str( Path( __file__ ).absolute().parents[ 2 ] ) )

from modules.db import psql

# home = expanduser('~')
# mypkey = paramiko.RSAKey.from_private_key_file(home + pkeyfilepath)
# if you want to use ssh password use - ssh_password='your ssh password', bellow

sql_hostname = '172.26.201.14'
sql_username = 'dbo_ro'
sql_password = 'RJYjIi2dB8z7mKWR0jzp'
sql_database = 't_monitor_prod'
sql_port = 5432

ssh_host = '31.28.163.25'
ssh_user = 'dbo_ro'
ssh_password = 'RJYjIi2dB8z7mKWR0jzp'
ssh_database = 't_monitor_prod'
ssh_port = 45632

# try:

with SSHTunnelForwarder(
        (ssh_host, ssh_port),
        ssh_username=ssh_user,
        ssh_password=ssh_password, 
        remote_bind_address=(sql_hostname, 5432)
        ) as server:
        
        server.start()
        print("server connected")

        params = {
            'host': 'localhost',
            'port': server.local_bind_port,
            'user': sql_username,
            'password': sql_password,
            'database': sql_database
            }

        conn = psycopg2.connect(**params)
        curs = conn.cursor()

        # curs.execute("SELECT VERSION();")
        curs.execute('SELECT * FROM parking_record ORDER BY time_created DESC LIMIT 100;')

        result = curs.fetchall()
        print(result)

        # Close connections
        conn.close()
        print("database connected")

# except:
#     print("Connection Failed")


# ssh -p 45632 dbo_ro@31.28.163.25 -L 172.26.201.14:5432:31.28.163.25:45632

# ssh_tunnel = SSHTunnelForwarder(
#         (ssh_host, ssh_port),
#         ssh_username=ssh_user,
#         ssh_password=ssh_password,
#         # ssh_pkey='/Users/aleksandrlozko/.ssh/id_rsa',
#         # ssh_port=ssh_port,
#         remote_bind_address=(sql_hostname, sql_port),
#         # local_bind_address=(sql_hostname, sql_port)
#         )

# ssh_tunnel.start() 

# db = psql.PostgreSQLDB(
#     host=sql_hostname,
#     port=sql_port,
#     type='PostgreSQLDB',
#     db=sql_database,
#     credentials=
#         {
#             'user': sql_username,
#             'password': sql_password
#         }
# )

# query = '''SELECT VERSION();'''
# data = db.execute(query)
# print(data)