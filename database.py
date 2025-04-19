import sqlite3
import random
import os

# Definim calea de bază a proiectului
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Creăm directorul data dacă nu există
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def init_db():
    db_path = os.path.join(DATA_DIR, 'users.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            apartment TEXT NOT NULL,
            amount_due REAL,
            amount_paid REAL DEFAULT 0,
            is_paid BOOLEAN DEFAULT 0
        )
    ''')
    
    # Verifică dacă există deja utilizatori
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        # Adaugă utilizatorii inițiali doar dacă tabela este goală
        fake_names = [
            "John Doe", "Jane Smith", "Alice Johnson", "Bob Brown", "Charlie Davis",
            "Diana Prince", "Ethan Hunt", "Fiona Gallagher", "George Costanza", "Hannah Montana"
        ]
        for i, name in enumerate(fake_names, 1):
            amount_due = random.uniform(50, 150)  # Generăm suma o singură dată pentru fiecare utilizator
            cursor.execute('INSERT INTO users (name, apartment, amount_due) VALUES (?, ?, ?)',
                       (name, str(i), amount_due))
    
    conn.commit()
    conn.close()

def get_users():
    db_path = os.path.join(DATA_DIR, 'users.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, apartment, amount_due, amount_paid, is_paid FROM users')
    users = cursor.fetchall()
    conn.close()
    # Convertim amount_due și amount_paid în float
    return [(user[0], user[1], user[2], float(user[3]), float(user[4]), user[5]) for user in users]

def add_user(name, apartment, amount_due):
    db_path = os.path.join(DATA_DIR, 'users.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (name, apartment, amount_due) VALUES (?, ?, ?)',
                   (name, apartment, amount_due))
    conn.commit()
    conn.close()

def delete_user(user_id):
    db_path = os.path.join(DATA_DIR, 'users.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

def get_fake_users():
    return get_users()  # Acum returnăm utilizatorii reali din baza de date

# --- Blocuri ---
def init_blocks_table():
    db_path = os.path.join(DATA_DIR, 'database.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_block(name, address):
    db_path = os.path.join(DATA_DIR, 'database.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO blocks (name, address) VALUES (?, ?)', (name, address))
    conn.commit()
    conn.close()

def get_blocks():
    db_path = os.path.join(DATA_DIR, 'database.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, address FROM blocks')
    blocks = [ {'id': row[0], 'name': row[1], 'address': row[2]} for row in cursor.fetchall() ]
    conn.close()
    return blocks

def delete_block(block_id):
    db_path = os.path.join(DATA_DIR, 'database.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM blocks WHERE id = ?', (block_id,))
    conn.commit()
    conn.close()