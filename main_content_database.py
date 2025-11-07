import sqlite3

conn = sqlite3.connect('premises.db', check_same_thread=False)
cursor = conn.cursor()

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

def add_object(address, area, floor, rooms_amount, price, image_path=None, created_by=None):
    local_conn = sqlite3.connect('premises.db')
    local_cursor = local_conn.cursor()

    local_cursor.execute('''
                SELECT * FROM houses WHERE address = ?
                ''', (address,))
    local_conn.commit()

    result = local_cursor.fetchone()

    if (result == None):
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
    local_conn = sqlite3.connect('premises.db')
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
    local_conn = sqlite3.connect('premises.db')
    local_cursor = local_conn.cursor()

    try:
        local_cursor.execute('''
                        SELECT * FROM houses WHERE id = ?
                        ''', (id,))
        result = local_cursor.fetchone()

        if (result != None):
            local_cursor.execute('''
                            DELETE FROM houses WHERE id = ?
                            ''', (id, ))
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
    local_conn = sqlite3.connect('premises.db')
    local_cursor = local_conn.cursor()

    try:
        local_cursor.execute('''
                UPDATE houses SET verified = 1 WHERE id = ?
                ''', (house_id,))
        local_conn.commit()
        return local_cursor.rowcount > 0
    except Exception as e:
        print(f"Error verifying object: {e}")
        return False
    finally:
        local_cursor.close()
        local_conn.close()

def get_user_group(username):
    local_conn = sqlite3.connect('users.db')
    local_cursor = local_conn.cursor()

    try:
        local_cursor.execute('''
                SELECT user_group FROM users WHERE username = ?
                ''', (username,))
        result = local_cursor.fetchone()
        return result[0] if result else 'user'
    except Exception as e:
        print(f"Error getting user group: {e}")
        return 'user'
    finally:
        local_cursor.close()
        local_conn.close()