import config
import mysql.connector

con = mysql.connector.connect(**config.db, database='servicemillion')
con.autocommit = True
