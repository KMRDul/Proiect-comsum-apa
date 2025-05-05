from flask import render_template, redirect, url_for, request, session
from functions.database import add_block, get_blocks, delete_block, get_db, get_users
from functions.auth import login_required

# Funcție pentru a asigura că există blocurile implicite în baza de date
# Această funcție verifică dacă blocurile standard există și le adaugă dacă nu
def ensure_default_blocks():
    # Obținem lista curentă de blocuri din baza de date
    blocks = get_blocks()
    
    # Definim blocurile implicite care ar trebui să existe în aplicație
    default_blocks = [
        {'name': 'Bloc A', 'address': 'Str. Libertății 12'},
        {'name': 'Bloc B', 'address': 'Bd. Unirii 5'},
        {'name': 'Bloc C', 'address': 'Str. Eminescu 8'}
    ]
    
    # Creăm un set cu numele și adresele blocurilor existente pentru căutare rapidă
    existing_names = set((b['name'], b['address']) for b in blocks)
    
    # Pentru fiecare bloc implicit, verificăm dacă există deja
    # Dacă nu există, îl adăugăm în baza de date
    for block in default_blocks:
        if (block['name'], block['address']) not in existing_names:
            add_block(block['name'], block['address'])

# Funcție pentru afișarea și gestionarea blocurilor
def manage_blocks():
    # Dacă este o cerere POST, procesez adăugarea sau ștergerea unui bloc
    if request.method == 'POST':
        # Verificăm dacă este o cerere de ștergere bloc
        if 'delete_block_id' in request.form:
            # Ștergem blocul cu ID-ul specificat
            delete_block(request.form['delete_block_id'])
            # Redirecționăm înapoi la pagina cu blocuri
            return redirect(url_for('blocuri'))
        else:
            # Altfel, este o cerere de adăugare bloc nou
            try:
                # Obținem numele și adresa blocului din formular
                name = request.form.get('block_name')
                address = request.form.get('block_address')
                # Verificăm dacă ambele câmpuri sunt completate
                if name and address:
                    # Adăugăm blocul nou în baza de date
                    add_block(name, address)
                    # Redirecționăm înapoi la pagina cu blocuri
                    return redirect(url_for('blocuri'))
            except Exception as e:
                # Logăm orice eroare apărută la adăugarea blocului
                print(f"Eroare la adăugare bloc: {e}")
    
    # Pentru cereri GET sau după procesarea POST-ului, afișăm lista de blocuri
    try:
        # Obținem toate blocurile din baza de date
        blocks = get_blocks()
        # Renderăm template-ul cu lista de blocuri și limba curentă
        return render_template('template2.html', blocks=blocks, language=session.get('language', 'ro'))
    except Exception as e:
        # Logăm și afișăm orice eroare apărută la obținerea blocurilor
        print(f"Eroare la afișare blocuri: {e}")
        return 'A apărut o eroare la afișarea blocurilor.', 500

# Funcție pentru afișarea detaliilor unui bloc și a locatarilor săi
def get_block_details(block_id):
    try:
        # Folosim funcțiile importate din functions.database
        # get_blocks și get_users sunt deja importate la începutul fișierului
        
        # Obținem toate blocurile și găsim blocul cu ID-ul specificat
        blocks = get_blocks()
        block = next((b for b in blocks if b['id'] == block_id), None)
        
        # Dacă blocul nu există, returnăm o eroare 404
        if not block:
            return 'Bloc inexistent', 404
            
        # Deschidem conexiunea la baza de date pentru consumul de apă
        water_db = get_db()
        
        # Obținem toți locatarii din blocul specificat
        users = get_users(block_id=block_id)
        
        # Această secțiune este protejată de try/except pentru a gestiona erorile
    except Exception as e:
        # Logăm și afișăm orice eroare apărută la obținerea datelor
        print(f"Eroare la afișare detalii bloc: {e}")
        return 'A apărut o eroare la afișarea detaliilor blocului.', 500
    
    # Pentru blocurile B și C (ID 2 și 3), amestecăm numele locatarilor pentru confidențialitate
    if block_id in [2, 3]:
        import random
        # Convertăm rezultatul la listă pentru a putea manipula datele
        users = list(users)
        users_shuffled = list(users)
        # Amestecăm lista pentru a obține nume aleatorii
        random.shuffle(users_shuffled)
        
        # Înlocuim doar numele locatarilor, păstrând celelalte date neschimbate
        users = [
            (user[0], users_shuffled[i][1], user[2], user[3], user[4], user[5])
            for i, user in enumerate(users)
        ]
        
        # Transformăm tuplurile în dicționare pentru a fi mai ușor de folosit în template
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
        # Pentru Bloc A sau alte blocuri, păstrăm datele originale
        # Transformăm tuplurile în dicționare doar dacă este necesar
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
    
    # Obținem datele despre consumul de apă pentru fiecare locatar
    water_data = {}
    for user in users:
        # Obținem ultimul consum înregistrat pentru fiecare locatar
        last_consumption = water_db.execute('''SELECT consumption FROM water_consumption 
                                           WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1''', 
                                        (user['id'],)).fetchone()
        # Salvăm consumul sau 0 dacă nu există înregistrări
        water_data[user['id']] = last_consumption['consumption'] if last_consumption else 0
    
    # Închide conexiunea la baza de date
    water_db.close()
    
    # Renderăm template-ul cu toate datele necesare
    # Transmitem lista de locatari, datele despre consum, prețul apei și informații despre bloc
    return render_template('template_page.html', users=users, water_data=water_data, water_price=6, block_id=block_id, block_name=block['name'], block_address=block['address'], block=block)
