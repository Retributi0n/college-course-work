# app_database.py
import sqlite3
import hashlib
import datetime
from datetime import datetime  # <- Так импортируется класс datetime

# Подключаемся к единой базе данных
conn = sqlite3.connect('databases/app.db', check_same_thread=False)
cursor = conn.cursor()

# Создаем таблицу пользователей
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR UNIQUE NOT NULL,
    password VARCHAR NOT NULL,
    user_group VARCHAR NOT NULL
)''')

# В начало файла, после других CREATE TABLE
cursor.execute('''
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    house_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    booking_id INTEGER UNIQUE,  -- Связь с конкретным бронированием
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (house_id) REFERENCES houses(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (booking_id) REFERENCES bookings(id),
    UNIQUE(user_id, house_id)  -- Один отзыв на дом от пользователя
)
''')
conn.commit()

# Создаем таблицу объектов недвижимости
cursor.execute('''
CREATE TABLE IF NOT EXISTS houses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    address VARCHAR UNIQUE NOT NULL,
    area VARCHAR NOT NULL,
    floor INTEGER NOT NULL,
    rooms_amount INTEGER NOT NULL,
    price VARCHAR NOT NULL,
    image_path VARCHAR DEFAULT NULL,
    verified BOOLEAN DEFAULT 0,
    created_by INTEGER,
    FOREIGN KEY (created_by) REFERENCES users(id)
)''')

conn.commit()

cursor.execute('''
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    house_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    start_date TEXT NOT NULL,    -- YYYY-MM-DD
    end_date TEXT NOT NULL,      -- YYYY-MM-DD
    total_price INTEGER NOT NULL,
    status TEXT DEFAULT 'active', -- active/cancelled/completed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (house_id) REFERENCES houses(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
)
''')
conn.commit()

# Создаем таблицу избранного
cursor.execute('''
CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    house_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (house_id) REFERENCES houses(id),
    UNIQUE(user_id, house_id)  -- Чтобы нельзя было добавить один дом дважды
)''')
conn.commit()


def add_booking(house_id, username, start_date, end_date, total_price):
    """Добавляет бронирование и возвращает ID или False"""
    conn = sqlite3.connect('databases/app.db')
    cursor = conn.cursor()

    # Получаем user_id по username
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user_result = cursor.fetchone()

    if not user_result:
        print(f"❌ Пользователь {username} не найден!")
        conn.close()
        return False

    user_id = user_result[0]
    print(f"✅ Найден user_id: {user_id} для пользователя {username}")

    try:
        # Проверяем доступность перед сохранением (только активные)
        if not check_booking_availability(house_id, start_date, end_date):
            print("❌ Дом уже занят на эти даты!")
            conn.close()
            return False

        # Проверяем, нет ли уже активного бронирования
        cursor.execute('''
            SELECT COUNT(*) FROM bookings 
            WHERE house_id = ? AND user_id = ? 
            AND start_date = ? AND end_date = ?
            AND status = 'active'
        ''', (house_id, user_id, start_date, end_date))

        if cursor.fetchone()[0] > 0:
            print("⚠️ Активное бронирование уже существует!")
            conn.close()
            return False

        # Вставляем новое бронирование с явным указанием status = 'active'
        cursor.execute('''
            INSERT INTO bookings (house_id, user_id, start_date, end_date, total_price, status)
            VALUES (?, ?, ?, ?, ?, 'active')
        ''', (house_id, user_id, start_date, end_date, total_price))
        conn.commit()

        booking_id = cursor.lastrowid
        print(f"✅ Бронирование сохранено! ID: {booking_id}")

        # Проверяем, что сохранилось
        cursor.execute("SELECT id, status FROM bookings WHERE id = ?", (booking_id,))
        saved = cursor.fetchone()
        print(f"📋 Проверка сохранения - ID: {saved[0]}, статус: {saved[1]}")

        return booking_id
    except Exception as e:
        print(f"❌ Ошибка бронирования: {e}")
        return False
    finally:
        conn.close()


def get_user_bookings(username, status=None):
    """Возвращает бронирования пользователя"""
    conn = sqlite3.connect('databases/app.db')
    cursor = conn.cursor()

    # Сначала проверим, есть ли пользователь
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if not user:
        print(f"❌ Пользователь {username} не найден")
        conn.close()
        return []

    user_id = user[0]
    print(f"📊 Загружаем бронирования для user_id: {user_id}")

    # Базовый запрос
    query = '''
        SELECT 
            b.id,
            b.house_id,
            h.address,
            h.image_path,
            b.start_date,
            b.end_date,
            b.total_price,
            b.status,
            b.created_at,
            h.price as price_per_night
        FROM bookings b
        JOIN houses h ON b.house_id = h.id
        WHERE b.user_id = ?
    '''
    params = [user_id]

    if status:
        query += ' AND b.status = ?'
        params.append(status)

    query += ' ORDER BY b.start_date DESC'

    print(f"🔍 SQL запрос: {query}")
    print(f"📌 Параметры: {params}")

    cursor.execute(query, params)
    rows = cursor.fetchall()
    print(f"📊 Найдено строк: {len(rows)}")

    # Преобразуем в список словарей
    bookings = []
    for row in rows:
        print(f"📦 Строка БД: {row}")

        # Вычисляем количество ночей
        from datetime import datetime
        start = datetime.strptime(row[4], '%Y-%m-%d')
        end = datetime.strptime(row[5], '%Y-%m-%d')
        nights = (end - start).days

        booking = {
            'id': row[0],
            'house_id': row[1],
            'address': row[2],
            'image_path': row[3],
            'start_date': row[4],
            'end_date': row[5],
            'total_price': row[6],
            'status': row[7],
            'created_at': row[8],
            'price_per_night': row[9],
            'nights': nights
        }
        print(f"✅ Создан объект бронирования: {booking}")
        bookings.append(booking)

    conn.close()
    return bookings

# Функции для работы с пользователями (из auth_database.py)
def add_user(username, password, user_group='user'):
    hash_object = hashlib.sha256(password.encode())
    hex_digest = hash_object.hexdigest()

    local_conn = sqlite3.connect('databases/app.db', check_same_thread=False)
    local_cursor = local_conn.cursor()

    local_cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    local_conn.commit()

    result = local_cursor.fetchone()

    if result is None:
        try:
            local_cursor.execute('''
            INSERT INTO users (username, password, user_group) VALUES (?, ?, ?)
            ''', (username, hex_digest, user_group))
            local_conn.commit()
            return True
        except Exception as e:
            print(f"Error adding user: {e}")
            return False
        finally:
            local_cursor.close()
            local_conn.close()
    else:
        return False

def search_user(username, password):
    hash_object = hashlib.sha256(password.encode())
    hex_digest = hash_object.hexdigest()

    local_conn = sqlite3.connect('databases/app.db', check_same_thread=False)
    local_cursor = local_conn.cursor()

    try:
        local_cursor.execute('''
        SELECT username, password FROM users WHERE username = ? AND password = ?
        ''', (username, hex_digest))
        local_conn.commit()

        result = local_cursor.fetchone()
        return result is not None
    except Exception as e:
        print(f"Error searching user: {e}")
        return False
    finally:
        local_cursor.close()
        local_conn.close()

# Функции для работы с объектами недвижимости (из main_content_database.py)
def add_object(address, area, floor, rooms_amount, price, image_path=None, created_by=None):
    local_conn = sqlite3.connect('databases/app.db')
    local_cursor = local_conn.cursor()

    local_cursor.execute('SELECT * FROM houses WHERE address = ?', (address,))
    local_conn.commit()

    result = local_cursor.fetchone()

    if result is None:
        try:
            local_cursor.execute('''
                INSERT INTO houses (address, area, floor, rooms_amount, price, image_path, verified, created_by) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (address, area, floor, rooms_amount, price, image_path, 0, created_by))
            local_conn.commit()
            return True
        except Exception as e:
            print(f"Error adding object: {e}")
            return False
        finally:
            local_cursor.close()
            local_conn.close()
    else:
        return False

def change_object_info(house_id, address, area, floor, rooms_amount, price, image_path=None):
    local_conn = sqlite3.connect('databases/app.db')
    local_cursor = local_conn.cursor()

    try:
        local_cursor.execute('''
                UPDATE houses 
                SET address = ?, area = ?, floor = ?, rooms_amount = ?, price = ?, image_path = ?
                WHERE id = ?
                ''', (address, area, floor, rooms_amount, price, image_path, house_id))
        local_conn.commit()
        return local_cursor.rowcount > 0
    except Exception as e:
        print(f"Error updating object: {e}")
        return False
    finally:
        local_cursor.close()
        local_conn.close()

def delete_object(id):
    local_conn = sqlite3.connect('databases/app.db')
    local_cursor = local_conn.cursor()

    try:
        local_cursor.execute('SELECT * FROM houses WHERE id = ?', (id,))
        result = local_cursor.fetchone()

        if result is not None:
            local_cursor.execute('DELETE FROM houses WHERE id = ?', (id,))
            local_conn.commit()
            return True
        else:
            return False
    except Exception as e:
        print(f"Error deleting object: {e}")
        return False
    finally:
        local_cursor.close()
        local_conn.close()

def verify_object(house_id):
    local_conn = sqlite3.connect('databases/app.db')
    local_cursor = local_conn.cursor()

    try:
        local_cursor.execute('UPDATE houses SET verified = 1 WHERE id = ?', (house_id,))
        local_conn.commit()
        return local_cursor.rowcount > 0
    except Exception as e:
        print(f"Error verifying object: {e}")
        return False
    finally:
        local_cursor.close()
        local_conn.close()

def get_user_group(username):
    local_conn = sqlite3.connect('databases/app.db')
    local_cursor = local_conn.cursor()

    try:
        local_cursor.execute('SELECT user_group FROM users WHERE username = ?', (username,))
        result = local_cursor.fetchone()
        return result[0] if result else 'user'
    except Exception as e:
        print(f"Error getting user group: {e}")
        return 'user'
    finally:
        local_cursor.close()
        local_conn.close()


# app_database.py (добавить в конец файла)

def get_user_bookings(username, status=None):
    """
    Возвращает бронирования пользователя с фильтром по статусу
    """
    conn = sqlite3.connect('databases/app.db')
    cursor = conn.cursor()

    query = '''
        SELECT 
            b.id,
            b.house_id,
            h.address,
            h.image_path,
            b.start_date,
            b.end_date,
            b.total_price,
            b.status,
            b.created_at,
            h.price as price_per_night,
            julianday(b.end_date) - julianday(b.start_date) as nights
        FROM bookings b
        JOIN houses h ON b.house_id = h.id
        JOIN users u ON b.user_id = u.id
        WHERE u.username = ?
    '''
    params = [username]

    if status:
        query += ' AND b.status = ?'
        params.append(status)

    query += ' ORDER BY b.start_date DESC'

    cursor.execute(query, params)
    bookings = cursor.fetchall()
    conn.close()

    # Преобразуем в список словарей для удобства
    result = []
    for b in bookings:
        result.append({
            'id': b[0],
            'house_id': b[1],
            'address': b[2],
            'image_path': b[3],
            'start_date': b[4],
            'end_date': b[5],
            'total_price': b[6],
            'status': b[7],
            'created_at': b[8],
            'price_per_night': b[9],
            'nights': int(b[10]) if b[10] else 0
        })

    return result


def cancel_booking(booking_id, username):
    """
    Отменяет бронирование (проверяет, что пользователь - владелец)
    """
    conn = sqlite3.connect('databases/app.db')
    cursor = conn.cursor()

    try:
        # Проверяем, что бронирование принадлежит пользователю и активно
        cursor.execute('''
            UPDATE bookings 
            SET status = 'cancelled' 
            WHERE id = ? AND user_id = (
                SELECT id FROM users WHERE username = ?
            ) AND status = 'active'
        ''', (booking_id, username))

        conn.commit()
        success = cursor.rowcount > 0

        if success:
            print(f"✅ Бронирование {booking_id} отменено")
        else:
            print(f"❌ Не удалось отменить бронирование {booking_id}")

        return success
    except Exception as e:
        print(f"Error cancelling booking: {e}")
        return False
    finally:
        conn.close()


def get_booking_details(booking_id, username):
    """
    Возвращает детальную информацию о бронировании
    """
    conn = sqlite3.connect('databases/app.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT 
            b.id,
            b.house_id,
            h.address,
            h.area,
            h.floor,
            h.rooms_amount,
            h.price as price_per_night,
            h.image_path,
            b.start_date,
            b.end_date,
            b.total_price,
            b.status,
            b.created_at,
            julianday(b.end_date) - julianday(b.start_date) as nights,
            u.username as owner_username
        FROM bookings b
        JOIN houses h ON b.house_id = h.id
        JOIN users u ON b.user_id = u.id
        WHERE b.id = ? AND u.username = ?
    ''', (booking_id, username))

    booking = cursor.fetchone()
    conn.close()

    if booking:
        return {
            'id': booking[0],
            'house_id': booking[1],
            'address': booking[2],
            'area': booking[3],
            'floor': booking[4],
            'rooms': booking[5],
            'price_per_night': booking[6],
            'image_path': booking[7],
            'start_date': booking[8],
            'end_date': booking[9],
            'total_price': booking[10],
            'status': booking[11],
            'created_at': booking[12],
            'nights': int(booking[13]) if booking[13] else 0,
            'owner': booking[14]
        }
    return None


def get_all_bookings_for_admin():
    """
    Для админа - все бронирования системы
    """
    conn = sqlite3.connect('databases/app.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT 
            b.id,
            u.username as user,
            h.address,
            b.start_date,
            b.end_date,
            b.total_price,
            b.status,
            b.created_at
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        JOIN houses h ON b.house_id = h.id
        ORDER BY b.created_at DESC
    ''')

    bookings = cursor.fetchall()
    conn.close()
    return bookings


def check_booking_availability(house_id, start_date, end_date, exclude_booking_id=None):
    """
    Проверяет, свободен ли дом на указанные даты
    Возвращает True, если свободно, False если занято
    """
    conn = sqlite3.connect('databases/app.db')
    cursor = conn.cursor()

    print(f"🔍 Проверка доступности: house_id={house_id}, {start_date} - {end_date}")

    # Проверяем ТОЛЬКО активные бронирования (status = 'active')
    # Отмененные (cancelled) и завершенные (completed) НЕ считаются!
    query = '''
        SELECT COUNT(*) FROM bookings 
        WHERE house_id = ? 
        AND status = 'active'  -- ВАЖНО: только активные!
        AND NOT (end_date < ? OR start_date > ?)
    '''
    params = [house_id, start_date, end_date]

    # Если редактируем бронирование, исключаем его из проверки
    if exclude_booking_id:
        query += ' AND id != ?'
        params.append(exclude_booking_id)

    cursor.execute(query, params)
    count = cursor.fetchone()[0]
    conn.close()

    print(f"📊 Найдено АКТИВНЫХ пересекающихся бронирований: {count}")
    return count == 0  # True если свободно (нет активных пересекающихся бронирований)


def update_booking_statuses():
    """
    Автоматически обновляет статусы бронирований
    (прошедшие становятся completed)
    """
    conn = sqlite3.connect('databases/app.db')
    cursor = conn.cursor()

    today = datetime.now().strftime('%Y-%m-%d')

    # Обновляем только active бронирования, у которых дата выезда уже прошла
    cursor.execute('''
        UPDATE bookings 
        SET status = 'completed' 
        WHERE status = 'active' AND end_date < ?
    ''', (today,))

    conn.commit()
    affected = cursor.rowcount
    conn.close()

    if affected > 0:
        print(f"✅ Обновлено {affected} бронирований на статус 'completed'")
    else:
        print(f"ℹ️ Нет бронирований для обновления")

    return affected


def get_booking_status(booking_id):
    """Возвращает статус бронирования"""
    conn = sqlite3.connect('databases/app.db')
    cursor = conn.cursor()

    cursor.execute("SELECT status FROM bookings WHERE id = ?", (booking_id,))
    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None


# ============ ФУНКЦИИ ДЛЯ ИЗБРАННОГО ============

def add_to_favorites(username, house_id):
    """
    Добавляет дом в избранное пользователя
    """
    conn = sqlite3.connect('databases/app.db')
    cursor = conn.cursor()

    try:
        # Получаем user_id
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if not user:
            print(f"❌ Пользователь {username} не найден")
            return False

        user_id = user[0]

        # Добавляем в избранное
        cursor.execute('''
            INSERT OR IGNORE INTO favorites (user_id, house_id)
            VALUES (?, ?)
        ''', (user_id, house_id))

        conn.commit()
        success = cursor.rowcount > 0

        if success:
            print(f"✅ Дом {house_id} добавлен в избранное пользователя {username}")
        else:
            print(f"ℹ️ Дом {house_id} уже в избранном")

        return success
    except Exception as e:
        print(f"❌ Ошибка при добавлении в избранное: {e}")
        return False
    finally:
        conn.close()


def remove_from_favorites(username, house_id):
    """
    Удаляет дом из избранного пользователя
    """
    conn = sqlite3.connect('databases/app.db')
    cursor = conn.cursor()

    try:
        # Получаем user_id
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if not user:
            print(f"❌ Пользователь {username} не найден")
            return False

        user_id = user[0]

        # Удаляем из избранного
        cursor.execute('''
            DELETE FROM favorites
            WHERE user_id = ? AND house_id = ?
        ''', (user_id, house_id))

        conn.commit()
        success = cursor.rowcount > 0

        if success:
            print(f"✅ Дом {house_id} удален из избранного пользователя {username}")
        else:
            print(f"ℹ️ Дом {house_id} не был в избранном")

        return success
    except Exception as e:
        print(f"❌ Ошибка при удалении из избранного: {e}")
        return False
    finally:
        conn.close()


def is_favorite(username, house_id):
    """
    Проверяет, находится ли дом в избранном у пользователя
    """
    conn = sqlite3.connect('databases/app.db')
    cursor = conn.cursor()

    try:
        # Получаем user_id
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if not user:
            return False

        user_id = user[0]

        # Проверяем наличие в избранном
        cursor.execute('''
            SELECT COUNT(*) FROM favorites
            WHERE user_id = ? AND house_id = ?
        ''', (user_id, house_id))

        count = cursor.fetchone()[0]
        return count > 0
    except Exception as e:
        print(f"❌ Ошибка при проверке избранного: {e}")
        return False
    finally:
        conn.close()


def get_user_favorites(username):
    """
    Возвращает список избранных домов пользователя
    """
    conn = sqlite3.connect('databases/app.db')
    cursor = conn.cursor()

    try:
        # Получаем user_id
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if not user:
            return []

        user_id = user[0]

        # Получаем все избранные дома с полной информацией
        cursor.execute('''
            SELECT h.* FROM houses h
            JOIN favorites f ON h.id = f.house_id
            WHERE f.user_id = ?
            ORDER BY f.created_at DESC
        ''', (user_id,))

        favorites = cursor.fetchall()
        print(f"📊 Загружено {len(favorites)} избранных домов для {username}")
        return favorites
    except Exception as e:
        print(f"❌ Ошибка при загрузке избранного: {e}")
        return []
    finally:
        conn.close()


def get_favorites_count(username):
    """
    Возвращает количество избранных домов у пользователя
    """
    conn = sqlite3.connect('databases/app.db')
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if not user:
            return 0

        user_id = user[0]

        cursor.execute('''
            SELECT COUNT(*) FROM favorites
            WHERE user_id = ?
        ''', (user_id,))

        return cursor.fetchone()[0]
    except Exception as e:
        print(f"❌ Ошибка при подсчете избранного: {e}")
        return 0
    finally:
        conn.close()


# ============ ФУНКЦИИ ДЛЯ ОТЗЫВОВ ============

def add_review(username, house_id, booking_id, rating, comment):
    """
    Добавляет отзыв о доме
    """
    conn = sqlite3.connect('databases/app.db')
    cursor = conn.cursor()

    try:
        # Получаем user_id
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if not user:
            print(f"❌ Пользователь {username} не найден")
            return False

        user_id = user[0]

        # Проверяем, не оставлял ли пользователь уже отзыв для этого дома
        cursor.execute('''
            SELECT id FROM reviews 
            WHERE user_id = ? AND house_id = ?
        ''', (user_id, house_id))

        if cursor.fetchone():
            print(f"⚠️ Пользователь уже оставлял отзыв для этого дома")
            return False

        # Добавляем отзыв
        cursor.execute('''
            INSERT INTO reviews (house_id, user_id, booking_id, rating, comment)
            VALUES (?, ?, ?, ?, ?)
        ''', (house_id, user_id, booking_id, rating, comment))

        conn.commit()
        review_id = cursor.lastrowid
        print(f"✅ Отзыв добавлен! ID: {review_id}")
        return review_id

    except Exception as e:
        print(f"❌ Ошибка при добавлении отзыва: {e}")
        return False
    finally:
        conn.close()


def get_house_reviews(house_id):
    """
    Возвращает все отзывы для конкретного дома
    """
    conn = sqlite3.connect('databases/app.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT 
            r.id,
            r.rating,
            r.comment,
            r.created_at,
            u.username,
            u.id as user_id
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        WHERE r.house_id = ?
        ORDER BY r.created_at DESC
    ''', (house_id,))

    reviews = cursor.fetchall()
    conn.close()

    # Преобразуем в список словарей
    result = []
    for r in reviews:
        result.append({
            'id': r[0],
            'rating': r[1],
            'comment': r[2],
            'created_at': r[3],
            'username': r[4],
            'user_id': r[5]
        })

    return result


def get_house_average_rating(house_id):
    """
    Возвращает средний рейтинг дома
    """
    conn = sqlite3.connect('databases/app.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT AVG(rating), COUNT(*) FROM reviews
        WHERE house_id = ?
    ''', (house_id,))

    avg, count = cursor.fetchone()
    conn.close()

    return {
        'average': round(avg, 1) if avg else 0,
        'count': count or 0
    }


def get_user_review_for_booking(username, booking_id):
    """
    Проверяет, оставлял ли пользователь отзыв для этого бронирования
    """
    conn = sqlite3.connect('databases/app.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT r.id, r.rating, r.comment, r.house_id
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        WHERE u.username = ? AND r.booking_id = ?
    ''', (username, booking_id))

    review = cursor.fetchone()
    conn.close()

    if review:
        return {
            'id': review[0],
            'rating': review[1],
            'comment': review[2],
            'house_id': review[3]
        }
    return None


def get_completed_bookings_for_review(username):
    """
    Возвращает завершенные бронирования, на которые можно оставить отзыв
    """
    conn = sqlite3.connect('databases/app.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT 
            b.id,
            b.house_id,
            h.address,
            b.start_date,
            b.end_date,
            b.total_price,
            (SELECT COUNT(*) FROM reviews WHERE booking_id = b.id) as has_review
        FROM bookings b
        JOIN houses h ON b.house_id = h.id
        JOIN users u ON b.user_id = u.id
        WHERE u.username = ? 
        AND b.status = 'completed'
        ORDER BY b.end_date DESC
    ''', (username,))

    bookings = cursor.fetchall()
    conn.close()

    result = []
    for b in bookings:
        result.append({
            'booking_id': b[0],
            'house_id': b[1],
            'address': b[2],
            'start_date': b[3],
            'end_date': b[4],
            'total_price': b[5],
            'has_review': b[6] > 0
        })

    return result