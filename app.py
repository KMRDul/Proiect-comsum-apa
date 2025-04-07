import os
import sqlite3
import logging
from cache import cache
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from database import init_db, add_user, get_fake_users, get_users
from functools import wraps
import random
from datetime import datetime
from jinja2 import FileSystemLoader
from api import get_romania_time

# Definim calea de bază a proiectului
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

# Creăm directoarele necesare dacă nu există
for directory in [DATA_DIR, TEMPLATE_DIR, STATIC_DIR]:
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError as e:
        logger.error(f"Error creating directory: {e}")

# Verificăm că template-urile există
print(f"Template directory: {TEMPLATE_DIR}")
print(f"Template files: {os.listdir(TEMPLATE_DIR)}")
print(f"Static directory: {STATIC_DIR}")
if os.path.exists(STATIC_DIR):
    print(f"Static files: {os.listdir(STATIC_DIR)}")

# Inițializăm aplicația Flask
app = Flask(__name__)
app.static_folder = STATIC_DIR
app.static_url_path = '/static'
app.jinja_loader = FileSystemLoader(TEMPLATE_DIR)
app.secret_key = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'

# Configurare logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_PATH = os.path.join(DATA_DIR, 'database.db')
USERS_DB_PATH = os.path.join(DATA_DIR, 'users.db')

def get_db():
    try:
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        db = sqlite3.connect(DATABASE_PATH)
        db.row_factory = sqlite3.Row
        return db
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise

def get_users_db():
    try:
        os.makedirs(os.path.dirname(USERS_DB_PATH), exist_ok=True)
        db = sqlite3.connect(USERS_DB_PATH)
        db.row_factory = sqlite3.Row
        return db
    except sqlite3.Error as e:
        logger.error(f"Users database connection error: {e}")
        raise

def init_water_db():
    try:
        with get_db() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS water_consumption
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          user_id INTEGER,
                          consumption REAL,
                          timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
            db.commit()
    except sqlite3.Error as e:
        logger.error(f"Failed to initialize water database: {e}")
        raise

# Initialize databases
try:
    init_db()
    init_water_db()
except sqlite3.Error as e:
    logger.error(f"Error initializing databases: {e}")

# Initierea cachingului
cache.init_app(app)

USER_CREDENTIALS = {
    'admin': 'admin'
}

@app.context_processor
def inject_language():
    return {'language': session.get('language', 'ro')}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            session['username'] = username
            session['language'] = session.get('language', 'ro')  # Setăm limba implicită la prima autentificare
            session.permanent = True
            return redirect(url_for('index'))
        else:
            flash('Credențiale incorecte!' if session.get('language', 'ro') == 'ro' else 'Invalid credentials!')
            return render_template('login.html', language=session.get('language', 'ro'))
    
    if 'username' in session:
        return redirect(url_for('index'))
        
    return render_template('login.html', language=session.get('language', 'ro'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    try:
        water_db = get_db()
        users_db = get_users_db()
        
        users = users_db.execute('SELECT * FROM users').fetchall()
        water_data = {}
        
        for user in users:
            last_consumption = water_db.execute('''SELECT consumption FROM water_consumption 
                                               WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1''', 
                                            (user['id'],)).fetchone()
            water_data[user['id']] = last_consumption['consumption'] if last_consumption else 0
        
        return render_template('index.html', users=users, water_data=water_data, water_price=6)
    except sqlite3.Error as e:
        logger.error(f"Database error in index route: {e}")
        flash('A apărut o eroare la accesarea datelor.' if session.get('language', 'ro') == 'ro' else 'An error occurred while accessing data.')
        return redirect(url_for('login'))
    finally:
        if 'water_db' in locals():
            water_db.close()
        if 'users_db' in locals():
            users_db.close()

@app.route('/update_water')
@login_required
def update_water():
    try:
        water_db = get_db()
        users_db = get_users_db()
        
        users = users_db.execute('SELECT id FROM users').fetchall()
        
        if not users:
            return jsonify({"status": "error", "message": "No users found"})
            
        selected_users = random.sample(users, min(3, len(users)))
        
        for user in users:
            if user in selected_users:
                consumption_increase = round(random.uniform(0.05, 0.15), 2)
            else:
                consumption_increase = 0
                
            last_consumption = water_db.execute('''SELECT consumption FROM water_consumption 
                                               WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1''', 
                                            (user['id'],)).fetchone()
            
            current_consumption = (last_consumption['consumption'] if last_consumption else 0) + consumption_increase
            
            water_db.execute('''INSERT INTO water_consumption (user_id, consumption) 
                            VALUES (?, ?)''', (user['id'], current_consumption))
        
        water_db.commit()
        return jsonify({"status": "success"})
    except sqlite3.Error as e:
        logger.error(f"Database error in update_water: {e}")
        return jsonify({"status": "error", "message": "Database error occurred"})
    except Exception as e:
        logger.error(f"Unexpected error in update_water: {e}")
        return jsonify({"status": "error", "message": "An unexpected error occurred"})
    finally:
        if 'water_db' in locals():
            water_db.close()
        if 'users_db' in locals():
            users_db.close()

@app.route('/update_payment/<int:user_id>', methods=['POST'])
@login_required
def update_payment(user_id):
    try:
        amount_paid = float(request.form['amount_paid'])
        
        users_db = get_users_db()
        
        users_db.execute('UPDATE users SET amount_paid = amount_paid + ? WHERE id = ?', 
                 (amount_paid, user_id))
        
        users_db.commit()
        return redirect(url_for('index'))
    except ValueError as e:
        logger.error(f"Invalid amount format: {e}")
        flash('Suma introdusă nu este validă!' if session.get('language', 'ro') == 'ro' else 'Invalid amount entered!')
        return redirect(url_for('index'))
    except sqlite3.Error as e:
        logger.error(f"Database error in update_payment: {e}")
        flash('Eroare la actualizarea plății!' if session.get('language', 'ro') == 'ro' else 'Error updating payment!')
        return redirect(url_for('index'))
    finally:
        if 'users_db' in locals():
            users_db.close()

@app.route('/change_language')
@login_required
def change_language():
    try:
        session['language'] = 'en' if session.get('language', 'ro') == 'ro' else 'ro'
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error changing language: {e}")
        flash('Eroare la schimbarea limbii!' if session.get('language', 'ro') == 'ro' else 'Error changing language!')
        return redirect(url_for('index'))

@app.route('/login_language')
def login_language():
    try:
        session['language'] = 'en' if session.get('language', 'ro') == 'ro' else 'ro'
        return redirect(url_for('login'))
    except Exception as e:
        logger.error(f"Error changing language: {e}")
        flash('Eroare la schimbarea limbii!' if session.get('language', 'ro') == 'ro' else 'Error changing language!')
        return redirect(url_for('login'))

@app.route('/api/time')
def time_endpoint():
    """Get current time in Romania"""
    try:
        return jsonify(get_romania_time())
    except Exception as e:
        logger.error(f"Error getting Romania time: {e}")
        return jsonify({"error": "Could not fetch time"}), 500

if __name__ == '__main__':
    try:
        app.run(debug=True)
    except Exception as e:
        logger.error(f"Error running the application: {e}")