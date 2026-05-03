import sqlite3
import os

DB_PATH = "queuelab.db"

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print(f" БД {DB_PATH} удалена")
else:
    print(f" Файл БД не найден")

print("Запустить сервер заново — БД создастся автоматически")