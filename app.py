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
    if not os.path.exists(directory):
        os.makedirs(directory)

# Verificăm că template-urile există
print(f"Template directory: {TEMPLATE_DIR}")
print(f"Template files: {os.listdir(TEMPLATE_DIR)}")
print(f"Static directory: {STATIC_DIR}")
if os.path.exists(STATIC_DIR):
    print(f"Static files: {os.listdir(STATIC_DIR)}")

# Inițializăm aplicația Flask
app = Flask(__name__)

# Configurăm aplicația
app.secret_key = 'your-secret-key-here'
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
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = sqlite3.Row
    return db

def get_users_db():
    os.makedirs(os.path.dirname(USERS_DB_PATH), exist_ok=True)
    db = sqlite3.connect(USERS_DB_PATH)
    db.row_factory = sqlite3.Row
    return db

def init_water_db():
    with get_db() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS water_consumption
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      consumption REAL,
                      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        db.commit()

def init_settings_db():
    with get_db() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS settings
                     (key TEXT PRIMARY KEY,
                      value TEXT)''')
        
        # Check if water_price setting exists
        result = db.execute('SELECT value FROM settings WHERE key = "water_price"').fetchone()
        if not result:
            # Insert default water price if it doesn't exist
            db.execute('INSERT INTO settings (key, value) VALUES ("water_price", "6.0")')
        db.commit()

# Initialize databases
init_db()
init_water_db()
init_settings_db()

# Initierea cachingului
cache.init_app(app)

USER_CREDENTIALS = {
    'admin': 'admin'
}

@app.context_processor
def inject_language():
    return dict(language=session.get('language', 'ro'))

def get_language():
    return session.get('language', 'ro')

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
    return redirect(url_for('tenants'))

@app.route('/tenants')
def tenants():
    users_db = get_users_db()
    users = users_db.execute('SELECT * FROM users').fetchall()
    water_price = get_water_price()
    
    # Get water consumption data
    db = get_db()
    water_consumption = db.execute('SELECT user_id, SUM(consumption) as total_consumption FROM water_consumption GROUP BY user_id').fetchall()
    
    # Create a dictionary mapping user_id to water consumption
    water_data = {}
    for item in water_consumption:
        water_data[item['user_id']] = item['total_consumption']
    
    return render_template('tenants.html', users=users, water_price=water_price, water_data=water_data, language=get_language())

@app.route('/reset_water_data')
@login_required
def reset_water_data():
    # Reset water consumption data
    db = get_db()
    db.execute('DELETE FROM water_consumption')
    db.commit()
    
    # Reset amount_paid for all users
    users_db = get_users_db()
    users_db.execute('UPDATE users SET amount_paid = 0')
    users_db.commit()
    users_db.close()
    
    flash('Consumul de apă și costurile au fost resetate la 0' if get_language() == 'ro' else 'Water consumption and costs have been reset to 0')
    return redirect(url_for('tenants'))

def get_water_price():
    db = get_db()
    result = db.execute('SELECT value FROM settings WHERE key = "water_price"').fetchone()
    return float(result['value']) if result else 6.0

@app.route('/get_buildings')
def get_buildings():
    # Return an empty list - no buildings will be shown
    buildings_list = []
    
    return jsonify(buildings_list)

@app.route('/building/<building_number>')
@login_required
def building(building_number):
    users_db = get_users_db()
    
    # Obține toți locatarii din blocul specificat
    users = users_db.execute(
        'SELECT id, apartment, name, amount_paid FROM users ' +
        'WHERE substr(apartment, 1, instr(apartment, "/")-1) = ? ' +
        'ORDER BY CAST(substr(apartment, instr(apartment, "/")+1) AS INTEGER)',
        (building_number,)
    ).fetchall()
    
    # Obține consumul de apă pentru locatarii găsiți
    users_list = []
    for user in users:
        # Verifică dacă există consum de apă pentru acest utilizator
        water_data = users_db.execute(
            'SELECT usage, month FROM water_consumption WHERE user_id = ? ' +
            'ORDER BY month DESC LIMIT 1',
            (user[0],)
        ).fetchone()
    
    # Construiește lista de utilizatori cu datele despre consum
    users_list = []
    for user in users:
        user_data = {
            'id': user[0],
            'apartment': user[1],
            'name': user[2],
            'amount_paid': user[3],
            'water_usage': None,
            'month': None
        }
        
        # Adaugă datele despre consumul de apă dacă există
        water_data = users_db.execute(
            'SELECT usage, month FROM water_consumption WHERE user_id = ? ' +
            'ORDER BY month DESC LIMIT 1',
            (user[0],)
        ).fetchone()
        
        if water_data:
            user_data['water_usage'] = water_data[0]
            user_data['month'] = water_data[1]
        
        users_list.append(user_data)
    
    # Verifică dacă există locatari în bloc
    if not users_list:
        return redirect(url_for('index'))
    
    users_db.close()
    
    return render_template('building.html',
                          users=users_list,
                          building_number=building_number,
                          water_price=6,
                          language=get_language())

@app.route('/add_building', methods=['POST'])
@login_required
def add_building():
    try:
        data = request.get_json()
        building = data.get('building')
        
        if not building:
            return jsonify({'error': 'Numărul blocului este obligatoriu' if session.get('language', 'ro') == 'ro' else 'Building number is required'}), 400
        
        users_db = get_users_db()
        
        # Verificăm dacă blocul există deja
        existing = users_db.execute(
            'SELECT 1 FROM users WHERE substr(apartment, 1, instr(apartment, "/")-1) = ?',
            (building,)
        ).fetchone()
        
        if existing:
            users_db.close()
            return jsonify({'error': 'Acest bloc există deja' if session.get('language', 'ro') == 'ro' else 'Building already exists'}), 400
        
        # Adăugăm un apartament inițial în bloc (de exemplu, apartamentul 1)
        users_db.execute('INSERT INTO users (apartment, name, amount_paid, water_usage) VALUES (?, "", 0, 0)',
                     (f'{building}/1',))
        users_db.commit()
        users_db.close()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/remove_building', methods=['POST'])
@login_required
def remove_building():
    try:
        data = request.get_json()
        building = data.get('building')
        
        if not building:
            return jsonify({'error': 'Numărul blocului este obligatoriu' if session.get('language', 'ro') == 'ro' else 'Building number is required'}), 400
        
        users_db = get_users_db()
        water_db = get_db()
        
        # Obținem toți utilizatorii din bloc pentru a le șterge și datele despre consum
        users = users_db.execute(
            'SELECT id FROM users WHERE substr(apartment, 1, instr(apartment, "/")-1) = ?',
            (building,)
        ).fetchall()
        
        # Ștergem datele despre consum pentru toți utilizatorii din bloc
        for user in users:
            water_db.execute('DELETE FROM water_consumption WHERE user_id = ?', (user['id'],))
        
        # Ștergem toți utilizatorii din bloc
        users_db.execute(
            'DELETE FROM users WHERE substr(apartment, 1, instr(apartment, "/")-1) = ?',
            (building,)
        )
        
        users_db.commit()
        water_db.commit()
        
        users_db.close()
        water_db.close()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/update_water')
@login_required
def update_water():
    water_db = get_db()
    users_db = get_users_db()
    
    # Obținem toți utilizatorii
    users = users_db.execute('SELECT id FROM users').fetchall()
    
    # Selectăm 3 utilizatori random
    selected_users = random.sample(users, min(3, len(users)))
    
    for user in users:
        if user in selected_users:
            # Doar utilizatorii selectați primesc o creștere a consumului
            consumption_increase = round(random.uniform(0.05, 0.15), 2)  # Creștem puțin intervalul pentru a face schimbarea mai vizibilă
        else:
            consumption_increase = 0  # Ceilalți utilizatori nu consumă apă în acest interval
            
        last_consumption = water_db.execute('''SELECT consumption FROM water_consumption 
                                           WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1''', 
                                        (user['id'],)).fetchone()
        
        current_consumption = (last_consumption['consumption'] if last_consumption else 0) + consumption_increase
        
        water_db.execute('''INSERT INTO water_consumption (user_id, consumption) 
                        VALUES (?, ?)''', (user['id'], current_consumption))
    
    water_db.commit()
    water_db.close()
    users_db.close()
    return jsonify({"status": "success"})

@app.route('/update_payment/<int:user_id>', methods=['POST'])
@login_required
def update_payment(user_id):
    amount_paid = float(request.form['amount_paid'])
    
    users_db = get_users_db()
    
    # Adăugăm suma plătită la totalul plătit de utilizator
    users_db.execute('UPDATE users SET amount_paid = amount_paid + ? WHERE id = ?', 
             (amount_paid, user_id))
    
    users_db.commit()
    users_db.close()
    
    return redirect(url_for('index'))

@app.route('/change_language')
@login_required
def change_language():
    session['language'] = 'en' if session.get('language', 'ro') == 'ro' else 'ro'
    return redirect(url_for('index'))

@app.route('/login_language')
def login_language():
    session['language'] = 'en' if session.get('language', 'ro') == 'ro' else 'ro'
    return redirect(url_for('login'))

@app.route('/api/time')
def time_endpoint():
    """Get current time in Romania"""
    return jsonify(get_romania_time())

@app.route('/add_user', methods=['POST'])
@login_required
def add_user_route():
    apartment = request.form.get('apartment')
    name = request.form.get('name')
    
    if not apartment or not name:
        flash('Toate câmpurile sunt obligatorii!' if session.get('language', 'ro') == 'ro' else 'All fields are required!')
        return redirect(url_for('index'))
    
    users_db = get_users_db()
    
    # Verifică dacă apartamentul există deja
    existing = users_db.execute('SELECT * FROM users WHERE apartment = ?', (apartment,)).fetchone()
    if existing:
        users_db.close()
        flash('Acest apartament există deja!' if session.get('language', 'ro') == 'ro' else 'This apartment already exists!')
        return redirect(url_for('index'))
    
    # Adaugă noul utilizator
    users_db.execute('INSERT INTO users (apartment, name, amount_paid) VALUES (?, ?, 0)', (apartment, name))
    users_db.commit()
    users_db.close()
    
    return redirect(url_for('index'))

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    users_db = get_users_db()
    water_db = get_db()
    
    # Șterge utilizatorul din baza de date users
    users_db.execute('DELETE FROM users WHERE id = ?', (user_id,))
    users_db.commit()
    
    # Șterge toate înregistrările de consum pentru acest utilizator
    water_db.execute('DELETE FROM water_consumption WHERE user_id = ?', (user_id,))
    water_db.commit()
    
    users_db.close()
    water_db.close()
    
    return jsonify({'status': 'success'})

print("test")
if __name__ == '__main__':
    app.run(debug=True)