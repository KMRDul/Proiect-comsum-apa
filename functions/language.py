from flask import session, redirect, url_for, request

# Procesor de context pentru a injecta limba curentă în toate template-urile
# Astfel, toate template-urile vor avea acces la variabila 'language'
def inject_language():
    return {'language': session.get('language', 'ro')}

# Funcție pentru schimbarea limbii aplicației pentru utilizatorii autentificați
def change_app_language():
    # Schimbă limba din română în engleză sau invers
    # Dacă limba curentă este română, o schimbă în engleză, altfel o schimbă în română
    session['language'] = 'en' if session.get('language', 'ro') == 'ro' else 'ro'
    
    # Verifică dacă există un parametru 'next' în URL pentru redirecționare
    next_url = request.args.get('next')
    if next_url:
        # Dacă există, redirecționează către acea pagină
        return redirect(next_url)
    # Altfel, redirecționează către pagina principală
    return redirect(url_for('index'))

# Funcție pentru schimbarea limbii pe pagina de login
def change_login_language():
    # Schimbă limba din română în engleză sau invers
    session['language'] = 'en' if session.get('language', 'ro') == 'ro' else 'ro'
    # Redirecționează înapoi la pagina de login
    return redirect(url_for('login'))
