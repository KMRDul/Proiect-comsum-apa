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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS water_consumption (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            usage REAL NOT NULL,
            month TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
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

def add_user(name, amount_due):
    db_path = os.path.join(DATA_DIR, 'users.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    apartment_number = cursor.fetchone()[0] + 1  # Crește cu 1 pentru a obține următorul număr de apartament
    cursor.execute('INSERT INTO users (name, apartment, amount_due) VALUES (?, ?, ?)',
                   (name, str(apartment_number), amount_due))
    conn.commit()
    conn.close()

def get_fake_users():
    return get_users()  # Acum returnăm utilizatorii reali din baza de date