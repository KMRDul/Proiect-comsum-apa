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

# Initialize databases
init_db()
init_water_db()

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
            session['language'] = session.get('language', 'ro')
            return redirect(url_for('blocuri'))
        else:
            flash('Credentiale incorecte!' if session.get('language', 'ro') == 'ro' else 'Invalid credentials!')
            return render_template('login.html', language=session.get('language', 'ro'))
    
    if 'username' in session:
        return redirect(url_for('blocuri'))
        
    return render_template('login.html', language=session.get('language', 'ro'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    water_db = get_db()
    users_db = get_users_db()
    
    users = users_db.execute('SELECT * FROM users').fetchall()
    water_data = {}
    
    for user in users:
        last_consumption = water_db.execute('''SELECT consumption FROM water_consumption 
                                           WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1''', 
                                        (user['id'],)).fetchone()
        water_data[user['id']] = last_consumption['consumption'] if last_consumption else 0
    
    water_db.close()
    users_db.close()
    return render_template('index.html', users=users, water_data=water_data, water_price=6)

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
    next_url = request.args.get('next')
    if next_url:
        return redirect(next_url)
    return redirect(url_for('index'))

@app.route('/login_language')
def login_language():
    session['language'] = 'en' if session.get('language', 'ro') == 'ro' else 'ro'
    return redirect(url_for('login'))

@app.route('/api/time')
def time_endpoint():
    """Get current time in Romania"""
    return jsonify(get_romania_time())

@app.route('/template')
def template_page():
    # Folosește același context de limbă ca pagina principală și trimite lista de utilizatori
    language = session.get('language', 'ro')
    water_db = get_db()
    users_db = get_users_db()
    users = users_db.execute('SELECT * FROM users').fetchall()
    water_data = {}
    for user in users:
        last_consumption = water_db.execute('''SELECT consumption FROM water_consumption \
                                           WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1''', \
                                        (user['id'],)).fetchone()
        water_data[user['id']] = last_consumption['consumption'] if last_consumption else 0
    water_db.close()
    users_db.close()
    return render_template('template_page.html', language=language, users=users, water_data=water_data, water_price=6)

from flask import redirect, url_for
from database import init_blocks_table, add_block, get_blocks, delete_block

# Inițializează tabela de blocuri la pornire și adaugă blocurile de bază dacă nu există
init_blocks_table()
def ensure_default_blocks():
    blocks = get_blocks()
    default_blocks = [
        {'name': 'Bloc A', 'address': 'Str. Libertății 12'},
        {'name': 'Bloc B', 'address': 'Bd. Unirii 5'},
        {'name': 'Bloc C', 'address': 'Str. Eminescu 8'}
    ]
    existing_names = set((b['name'], b['address']) for b in blocks)
    for block in default_blocks:
        if (block['name'], block['address']) not in existing_names:
            add_block(block['name'], block['address'])
ensure_default_blocks()

# Pagina cu blocurile manageriate de utilizator
@app.route('/blocuri', methods=['GET', 'POST'])
@login_required
def blocuri():
    if request.method == 'POST':
        if 'delete_block_id' in request.form:
            delete_block(request.form['delete_block_id'])
            return redirect(url_for('blocuri'))
        else:
            try:
                name = request.form.get('block_name')
                address = request.form.get('block_address')
                if name and address:
                    add_block(name, address)
                    return redirect(url_for('blocuri'))
            except Exception as e:
                print(f"Eroare la adăugare bloc: {e}")
    try:
        blocks = get_blocks()
        return render_template('template2.html', blocks=blocks, language=session.get('language', 'ro'))
    except Exception as e:
        print(f"Eroare la afișare blocuri: {e}")
        return 'A apărut o eroare la afișarea blocurilor.', 500

# Detalii bloc (mock)
@app.route('/bloc/<int:block_id>/add_tenant', methods=['POST'])
@login_required
def add_tenant(block_id):
    try:
        apartment = request.form['apartment']
        name = request.form['name']
        amount_due = 100
        from database import add_user
        add_user(name, apartment, amount_due, block_id)
        return redirect(url_for('block_detail', block_id=block_id))
    except Exception as e:
        print(f"Eroare la adăugare locatar: {e}")
        return 'A apărut o eroare la adăugarea locatarului.', 500

@app.route('/bloc/<int:block_id>')
@login_required
def block_detail(block_id):
    try:
        from database import get_blocks, get_users
        blocks = get_blocks()
        block = next((b for b in blocks if b['id'] == block_id), None)
        if not block:
            return 'Bloc inexistent', 404
        water_db = get_db()
        users = get_users(block_id=block_id)
        # Scramble numele locatarilor doar pentru Bloc B și Bloc C
        # restul funcției rămâne neschimbat
        # ...
        # (nu modificăm aici, doar protejăm începutul cu try)
    except Exception as e:
        print(f"Eroare la afișare detalii bloc: {e}")
        return 'A apărut o eroare la afișarea detaliilor blocului.', 500
    if block_id in [2, 3]:
        import random
        users = list(users)
        users_shuffled = list(users)
        random.shuffle(users_shuffled)
        # Înlocuim doar numele, restul datelor rămân la fel
        users = [
            (user[0], users_shuffled[i][1], user[2], user[3], user[4], user[5])
            for i, user in enumerate(users)
        ]
        # Transformăm tuplurile în dict-uri pentru template
        users = [
            {
                'id': u[0],
                'name': u[1],
                'apartment': u[2],
                'amount_due': u[3],
                'amount_paid': u[4],
                'is_paid': u[5]
            }
            for u in users
        ]
    else:
        # Pentru Bloc A sau altele, transformăm doar dacă nu e deja dict
        if users and isinstance(users[0], tuple):
            users = [
                {
                    'id': u[0],
                    'name': u[1],
                    'apartment': u[2],
                    'amount_due': u[3],
                    'amount_paid': u[4],
                    'is_paid': u[5]
                }
                for u in users
            ]
    water_data = {}
    for user in users:
        last_consumption = water_db.execute('''SELECT consumption FROM water_consumption 
                                           WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1''', 
                                        (user['id'],)).fetchone()
        water_data[user['id']] = last_consumption['consumption'] if last_consumption else 0
    water_db.close()
    return render_template('template_page.html', users=users, water_data=water_data, water_price=6, block_id=block_id, block_name=block['name'], block_address=block['address'], block=block)

@app.route('/delete_tenant/<int:user_id>', methods=['POST'])
@login_required
def delete_tenant(user_id):
    from database import delete_user
    delete_user(user_id)
    from flask import request
    return redirect(request.referrer or url_for('index'))

print("test")
if __name__ == '__main__':
    app.run(debug=True)