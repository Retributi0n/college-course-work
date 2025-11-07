import sqlite3
import hashlib

conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

# Создаем таблицу, если она не существует
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR UNIQUE NOT NULL,
    password VARCHAR NOT NULL,
    user_group VARCHAR NOT NULL
)''')

conn.commit()

def add_user(username, password, user_group='user'):  # Добавляем параметр группы
    hash_object = hashlib.sha256(password.encode())
    hex_digest= hash_object.hexdigest()

    local_conn = sqlite3.connect('users.db')
    local_cursor = local_conn.cursor()

    local_cursor.execute('''
            SELECT * FROM users WHERE username = ?
            ''', (username,))
    local_conn.commit()

    result = local_cursor.fetchone()

    if (result == None):
        try:
            local_cursor.execute('''
            INSERT INTO users (username, password, user_group) VALUES (?, ?, ?)
            ''', (username, hex_digest, user_group))  # Используем переданную группу
            local_conn.commit()

        finally:
            local_cursor.close()
            local_conn.close()

        return True

    else:
        return False

def search_user(username, password):
    hash_object = hashlib.sha256(password.encode())
    hex_digest = hash_object.hexdigest()

    local_conn = sqlite3.connect('users.db')
    local_cursor = local_conn.cursor()

    try:
        local_cursor.execute('''
        SELECT username, password FROM users WHERE username = ? AND password = ?
        ''', (username, hex_digest))
        local_conn.commit()

        result = local_cursor.fetchone()
        if result != None:
            return True
        else:
            return False

    finally:
        local_cursor.close()
        local_conn.close()
