import os
import sqlite3
import random

# Importăm variabilele de cale din app.py
# Acestea vor fi disponibile după importarea acestui modul în app.py
DATABASE_PATH = None
USERS_DB_PATH = None
DATA_DIR = None

# Funcție pentru setarea căilor către bazele de date
# Aceasta va fi apelată din app.py pentru a inițializa căile
def set_db_paths(database_path, users_db_path, data_dir=None):
    global DATABASE_PATH, USERS_DB_PATH, DATA_DIR
    DATABASE_PATH = database_path
    USERS_DB_PATH = users_db_path
    DATA_DIR = data_dir

# Funcție pentru obținerea unei conexiuni la baza de date principală
# Creează folderul dacă nu există și setează Row Factory pentru a accesa coloanele după nume
def get_db():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = sqlite3.Row
    return db

# Funcție pentru obținerea unei conexiuni la baza de date pentru utilizatori
# Creează folderul dacă nu există și setează Row Factory pentru a accesa coloanele după nume
def get_users_db():
    os.makedirs(os.path.dirname(USERS_DB_PATH), exist_ok=True)
    db = sqlite3.connect(USERS_DB_PATH)
    db.row_factory = sqlite3.Row
    return db

# Funcție pentru inițializarea bazei de date pentru consumul de apă
# Creează tabela water_consumption dacă nu există deja
def init_water_db():
    with get_db() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS water_consumption
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      consumption REAL,
                      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        db.commit()

# Funcție pentru inițializarea bazei de date de utilizatori
def init_db():
    os.makedirs(os.path.dirname(USERS_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(USERS_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            apartment TEXT NOT NULL,
            amount_due REAL,
            amount_paid REAL DEFAULT 0,
            is_paid BOOLEAN DEFAULT 0,
            block_id INTEGER NOT NULL
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
            cursor.execute('INSERT INTO users (name, apartment, amount_due, block_id) VALUES (?, ?, ?, ?)',
                       (name, str(i), amount_due, 1))  # Demo: toți inițial în blocul 1
    
    conn.commit()
    conn.close()

# Funcție pentru obținerea utilizatorilor din baza de date
def get_users(block_id=None):
    conn = sqlite3.connect(USERS_DB_PATH)
    cursor = conn.cursor()
    if block_id is not None:
        cursor.execute('SELECT id, name, apartment, amount_due, amount_paid, is_paid FROM users WHERE block_id = ?', (block_id,))
    else:
        cursor.execute('SELECT id, name, apartment, amount_due, amount_paid, is_paid FROM users')
    users = cursor.fetchall()
    conn.close()
    # Convertim amount_due și amount_paid în float
    return [(user[0], user[1], user[2], float(user[3]), float(user[4]), user[5]) for user in users]

# Funcție pentru adăugarea unui utilizator în baza de date
def add_user(name, apartment, amount_due, block_id):
    conn = sqlite3.connect(USERS_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (name, apartment, amount_due, block_id) VALUES (?, ?, ?, ?)',
                   (name, apartment, amount_due, block_id))
    conn.commit()
    conn.close()

# Funcție pentru ștergerea unui utilizator din baza de date
def delete_user(user_id):
    conn = sqlite3.connect(USERS_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

# Funcție pentru obținerea utilizatorilor fictivi (acum returnează utilizatorii reali)
def get_fake_users():
    return get_users()  # Acum returnăm utilizatorii reali din baza de date

# Funcție de compatibilitate pentru script-uri vechi
def init_users_table():
    init_db()

# --- Blocuri ---
# Funcție pentru inițializarea tabelei de blocuri
def init_blocks_table():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
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

# Funcție pentru adăugarea unui bloc în baza de date
def add_block(name, address):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO blocks (name, address) VALUES (?, ?)', (name, address))
    conn.commit()
    conn.close()

# Funcție pentru obținerea blocurilor din baza de date
def get_blocks():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, address FROM blocks')
    blocks = [ {'id': row[0], 'name': row[1], 'address': row[2]} for row in cursor.fetchall() ]
    conn.close()
    return blocks

# Funcție pentru ștergerea unui bloc din baza de date
def delete_block(block_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM blocks WHERE id = ?', (block_id,))
    conn.commit()
    conn.close()
