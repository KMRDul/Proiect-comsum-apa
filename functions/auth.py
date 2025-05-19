from flask import session, redirect, url_for, render_template, flash, request
from functools import wraps

# Credentialele utilizatorilor pentru autentificare
# În producție, ar trebui să folosim o metodă mai sigură (bază de date, hash-uri pentru parole)
USER_CREDENTIALS = {
    'admin': 'admin'
}

# Decorator pentru a proteja rutele care necesită autentificare
# Redirecționează către pagina de login dacă utilizatorul nu este autentificat
def login_required(f):
    @wraps(f)  # Păstrează metadatele funcției originale
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Funcție pentru procesarea cererii de login
def process_login():
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

# Funcție pentru procesarea cererii de logout
def process_logout():
    session.pop('username', None)
    return redirect(url_for('login'))
