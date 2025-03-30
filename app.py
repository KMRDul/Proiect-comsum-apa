import sqlite3
import os
from cache import cache
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from database import init_db, add_user, get_fake_users, get_users
from functools import wraps
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'

# Database configuration
DATABASE_PATH = os.path.join('data', 'database.db')
USERS_DB_PATH = os.path.join('data', 'users.db')

def get_db():
    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = sqlite3.Row
    return db

def get_users_db():
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
            session['language'] = session.get('language', 'ro')  # Setăm limba implicită la prima autentificare
            session.permanent = True
            return redirect(url_for('index'))
        else:
            flash('Credențiale incorecte!' if session.get('language', 'ro') == 'ro' else 'Invalid credentials!')
            return render_template('login.html')
    
    if 'username' in session:
        return redirect(url_for('index'))
        
    return render_template('login.html')

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
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)