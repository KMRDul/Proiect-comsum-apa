from flask import jsonify, render_template, session
from datetime import datetime
import pytz
from functions.database import get_db, get_users_db

# Funcție pentru obținerea orei curente din România
def get_romania_time():
    """Get current time in Romania (only hours and minutes)"""
    romania_tz = pytz.timezone('Europe/Bucharest')
    current_time = datetime.now(romania_tz)
    return {
        'hour': current_time.hour,
        'minute': current_time.minute
    }

# Funcție pentru obținerea orei curente din România ca răspuns JSON
def get_current_time():
    return jsonify(get_romania_time())

# Funcție pentru afișarea paginii de template demonstrativă
def render_template_page():
    # Obținem limba curentă din sesiune (implicit română)
    language = session.get('language', 'ro')

    water_db = get_db()
    users_db = get_users_db()
    
    # Obținem toți utilizatorii din baza de date
    users = users_db.execute('SELECT * FROM users').fetchall()

    # Dicționar pentru stocarea datelor despre consumul de apă pentru fiecare utilizator
    water_data = {}
    
    # Pentru fiecare utilizator, obținem ultimul consum de apă înregistrat
    for user in users:
        last_consumption = water_db.execute('''SELECT consumption FROM water_consumption \
                                           WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1''', \
                                        (user['id'],)).fetchone()
        # Salvăm consumul sau 0 dacă nu există înregistrări
        water_data[user['id']] = last_consumption['consumption'] if last_consumption else 0

    water_db.close()
    users_db.close()

    return render_template('template_page.html', language=language, users=users, water_data=water_data, water_price=6)
