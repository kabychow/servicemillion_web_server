from helper.database import config
import mysql.connector


class Connection:
    def __init__(self):
        self.con = mysql.connector.connect(**config.db)
        self.con.autocommit = True
