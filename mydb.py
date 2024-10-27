import sqlite3
from asgiref.sync import sync_to_async
import asyncio


class SQLighter:
    def __init__(self, database='mytt.db'):
        self.database = database

    def connect(self):
        return sqlite3.connect(self.database)


@sync_to_async
def get_info(user_id):
    with SQLighter().connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM timetable WHERE user_id = ?", (user_id,))
        return cursor.fetchall()


@sync_to_async
def add_new_appt(user_id, name, phone, animal_type, doctor, problem):
    with SQLighter().connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO timetable (user_id, fio, phone_number, animal_type, doctor, problem) VALUES(?,?,?,?,?,?)",
            (user_id, name, phone, animal_type, doctor, problem)
        )
        conn.commit()


@sync_to_async
def create_table():
    with SQLighter().connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS timetable(user_id TEXT, fio TEXT, phone_number TEXT, animal_type TEXT, "
            "doctor TEXT, problem TEXT)")
        conn.commit()

