import sqlite3
import os


class Database:
    connection = None
    __DATABASE_LOCATION = os.path.join(os.path.dirname(__file__), '..', 'blockchain.db')

    def __init__(self):
        self.connection = sqlite3.connect(self.__DATABASE_LOCATION)

    def execute(self,sql, object=None):
        cursor = self.connection.cursor()
        cursor.execute(sql)
        self.connection.commit()
        return cursor.lastrowid

    def close_connection(self):
        self.connection.close()
