import psycopg2
import os
from dotenv import load_dotenv


class Database:
    def __init__(self):
        load_dotenv()
        password = os.getenv('DB_PASS')
        self.conn = psycopg2.connect(database="SavvyRPG",
                                    host="localhost",
                                    user="postgres",
                                    password=f"{password}",
                                    port="5432")
        self.cur = self.conn.cursor()
