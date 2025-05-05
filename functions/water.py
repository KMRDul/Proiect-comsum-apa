import random
from flask import jsonify
from functions.database import get_db, get_users_db

# Funcție pentru afișarea paginii principale cu consumul de apă
def get_water_data():
    # Deschidem conexiunile la bazele de date
    water_db = get_db()
    users_db = get_users_db()
    
    # Obținem toți utilizatorii din baza de date
    users = users_db.execute('SELECT * FROM users').fetchall()
    # Dicționar pentru stocarea datelor despre consumul de apă pentru fiecare utilizator
    water_data = {}
    
    # Pentru fiecare utilizator, obținem ultimul consum de apă înregistrat
    for user in users:
        last_consumption = water_db.execute('''SELECT consumption FROM water_consumption 
                                           WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1''', 
                                         (user['id'],)).fetchone()
        # Salvăm consumul sau 0 dacă nu există înregistrări
        water_data[user['id']] = last_consumption['consumption'] if last_consumption else 0
    
    # Închide conexiunile la bazele de date
    water_db.close()
    users_db.close()
    
    return users, water_data

# Funcție pentru actualizarea consumului de apă
def update_water_consumption():
    # Actualizăm consumul de apă pentru utilizatori
    # Deschidem conexiunile la bazele de date
    water_db = get_db()
    users_db = get_users_db()
    
    # Obținem toți utilizatorii din baza de date
    users = users_db.execute('SELECT id FROM users').fetchall()
    
    # Selectăm aleatoriu 3 utilizatori (sau mai puțini dacă nu sunt suficienți) 
    # care vor primi o creștere a consumului de apă
    selected_users = random.sample(users, min(3, len(users)))
    
    # Parcurgem fiecare utilizator pentru a actualiza consumul
    for user in users:
        if user in selected_users:
            # Doar utilizatorii selectați aleatoriu primesc o creștere a consumului
            # Generăm o valoare aleatorie între 0.05 și 0.15 pentru creșterea consumului
            consumption_increase = round(random.uniform(0.05, 0.15), 2)  # Rotunjim la 2 zecimale
        else:
            # Ceilalți utilizatori nu primesc creștere de consum în această iterație
            consumption_increase = 0
            
        # Obținem ultimul consum înregistrat pentru utilizator
        last_consumption = water_db.execute('''SELECT consumption FROM water_consumption 
                                           WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1''', 
                                        (user['id'],)).fetchone()
        
        # Calculăm noul consum adăugând creșterea la consumul anterior
        # Dacă nu există un consum anterior, începem de la 0
        current_consumption = (last_consumption['consumption'] if last_consumption else 0) + consumption_increase
        
        # Inserăm noua valoare a consumului în baza de date
        water_db.execute('''INSERT INTO water_consumption (user_id, consumption) 
                        VALUES (?, ?)''', (user['id'], current_consumption))
    
    # Salvăm modificările în baza de date
    water_db.commit()
    # Închidem conexiunile la bazele de date
    water_db.close()
    users_db.close()
    # Returnăm un răspuns JSON cu status de succes
    return jsonify({"status": "success"})

# Funcție pentru actualizarea plăților unui utilizator
def update_user_payment(user_id, amount_paid):
    # Obținem suma plătită din formular și o convertim la tip float
    amount_paid = float(amount_paid)
    
    # Deschidem conexiunea la baza de date cu utilizatori
    users_db = get_users_db()
    
    # Actualizăm suma totală plătită de utilizator prin adăugarea noii plăți
    # la suma existentă în baza de date
    users_db.execute('UPDATE users SET amount_paid = amount_paid + ? WHERE id = ?', 
             (amount_paid, user_id))
    
    # Salvăm modificările în baza de date
    users_db.commit()
    # Închide conexiunea la baza de date
    users_db.close()
