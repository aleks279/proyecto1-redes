#!/usr/bin/python
import mysql.connector as mariadb
#retrieving information
ip = '127.0.0.1'
cursor.execute("SELECT * FROM nodes WHERE ip=%s", (ip))

for host, date in cursor:
    print("Host Name: {}, Date: {}").format(host,date)

