#!/usr/bin/python
import mysql.connector as mariadb

mariadb_connection = mariadb.connect(user='raspi', password='@1234abc', database='nodes')
cursor = mariadb_connection.cursor()
