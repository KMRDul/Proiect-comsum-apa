from flask import session, redirect, url_for, request

# Procesor de context pentru a injecta limba curentă în toate template-urile
# Astfel, toate template-urile vor avea acces la variabila 'language'
def inject_language():
    return {'language': session.get('language', 'ro')}

# Funcție pentru schimbarea limbii aplicației pentru utilizatorii autentificați
def change_app_language():
    session['language'] = 'en' if session.get('language', 'ro') == 'ro' else 'ro'
    
    # Verifică dacă există un parametru 'next' în URL pentru redirecționare
    next_url = request.args.get('next')
    if next_url:
        return redirect(next_url)
    return redirect(url_for('index'))

# Funcție pentru schimbarea limbii pe pagina de login
def change_login_language():
    session['language'] = 'en' if session.get('language', 'ro') == 'ro' else 'ro'
    return redirect(url_for('login'))
