#!/usr/bin/python
import mysql.connector as mariadb

define insertNode(host, ip):
    #insert information
    try:
        cursor.execute("INSERT INTO nodes (host,ip,date_last) VALUES (%s,%s,%s)", (host,ip))
    except mariadb.Error as error:
        print("Error: {}".format(error))

    mariadb_connection.commit()
    print "The last inserted id was: ", cursor.lastrowid

    mariadb_connection.close()
