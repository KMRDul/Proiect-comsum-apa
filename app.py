import os  # pentru operații cu sistemul de fișiere
import logging  # pentru logarea evenimentelor
from functions.cache import cache
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from jinja2 import FileSystemLoader  # pentru încărcarea template-urilor Jinja2

from functions.database import set_db_paths, get_db, get_users_db, init_water_db, init_db, init_blocks_table
from functions.database import add_user, get_users, get_fake_users, delete_user
from functions.database import add_block, get_blocks, delete_block
from functions.auth import login_required, process_login, process_logout
from functions.water import get_water_data, update_water_consumption, update_user_payment
from functions.language import inject_language, change_app_language, change_login_language
from functions.blocks import ensure_default_blocks, manage_blocks, get_block_details
from functions.tenants import add_tenant_to_block, delete_tenant_from_block
from functions.api import get_current_time, render_template_page

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

# Creăm directoarele necesare dacă nu există deja
for directory in [DATA_DIR, TEMPLATE_DIR, STATIC_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Afișăm în consolă informații despre directoarele de template-uri și fișiere statice (pentru depanare)
print(f"Template directory: {TEMPLATE_DIR}")
print(f"Template files: {os.listdir(TEMPLATE_DIR)}")
print(f"Static directory: {STATIC_DIR}")

if os.path.exists(STATIC_DIR):
    print(f"Static files: {os.listdir(STATIC_DIR)}")

# Inițializăm aplicația Flask și configurăm directoarele pentru fișiere statice și template-uri
app = Flask(__name__)
app.static_folder = STATIC_DIR  # setăm folderul pentru fișiere statice
app.static_url_path = '/static'  # URL-ul pentru accesarea fișierelor statice
app.jinja_loader = FileSystemLoader(TEMPLATE_DIR)  # încărcăm template-urile din folderul specificat
app.secret_key = os.urandom(24)  # cheia secretă pentru sesiuni
app.config['SESSION_TYPE'] = 'filesystem'  # stocăm sesiunile pe disc

# Configurăm logging-ul aplicației pentru depanare
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Definim căile către bazele de date folosite în aplicație
DATABASE_PATH = os.path.join(DATA_DIR, 'database.db')
USERS_DB_PATH = os.path.join(DATA_DIR, 'users.db')

# Setăm căile către bazele de date în modulul functions.database
set_db_paths(DATABASE_PATH, USERS_DB_PATH, DATA_DIR)

# Inițializăm bazele de date la pornirea aplicației
# init_db() este importată din modulul database.py și creează tabela de utilizatori
# init_water_db() creează tabela pentru consumul de apă
init_db()
init_water_db()

cache.init_app(app)

@app.context_processor
def inject_language_context():
    return inject_language()

# Ruta pentru pagina de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    return process_login()

# Ruta pentru delogare
@app.route('/logout')
def logout():
    return process_logout()

# Ruta principală a aplicației
# Necesită autentificare pentru a fi accesată
@app.route('/')
@login_required
def index():
    # Obținem datele despre utilizatori și consumul de apă
    users, water_data = get_water_data()

    # Renderăm template-ul index.html cu datele obținute. Prețul apei este setat la 6 lei/unitate.
    return render_template('index.html', users=users, water_data=water_data, water_price=6)

# Rută pentru actualizarea consumului de apă
# Simulează consumul de apă pentru utilizatori (pentru demonstrație)
@app.route('/update_water')
@login_required
def update_water():
    return update_water_consumption()

# Rută pentru actualizarea plăților unui utilizator
# Permite administratorului să înregistreze plățile efectuate de locatari
@app.route('/update_payment/<int:user_id>', methods=['POST'])
@login_required
def update_payment(user_id):
    amount_paid = request.form['amount_paid']
    update_user_payment(user_id, amount_paid)
    return redirect(url_for('index'))

# Rută pentru schimbarea limbii aplicației pentru utilizatorii autentificați
# Permite comutarea între română și engleză
@app.route('/change_language')
@login_required
def change_language():
    return change_app_language()

# Rută pentru schimbarea limbii pe pagina de login
# Permite comutarea între română și engleză înainte de autentificare
@app.route('/login_language')
def login_language():
    return change_login_language()

# Rută API pentru obținerea orei curente din România
# Returnează ora în format JSON
@app.route('/api/time')
def time_endpoint():
    return get_current_time()

# Rută pentru pagina de template demonstrativă
# Afișează datele utilizatorilor în template-ul template_page.html
@app.route('/template')
def template_page():
    return render_template_page()

init_blocks_table()

ensure_default_blocks()

# Pagina cu blocurile manageriate de utilizator (pagina principală după autentificare)
# Permite vizualizarea, adăugarea și ștergerea blocurilor
@app.route('/blocuri', methods=['GET', 'POST'])
@login_required
def blocuri():
    return manage_blocks()

# Rută pentru adăugarea unui locatar în bloc
# Permite administratorului să adauge un nou locatar în blocul specificat
@app.route('/bloc/<int:block_id>/add_tenant', methods=['POST'])
@login_required
def add_tenant(block_id):
    return add_tenant_to_block(block_id)

# Rută pentru afișarea detaliilor unui bloc și a locatarilor săi
# Afișează informații despre bloc și lista locatarilor cu consumul lor de apă
@app.route('/bloc/<int:block_id>')
@login_required
def block_detail(block_id):
    return get_block_details(block_id)

# Rută pentru ștergerea unui locatar din baza de date
# Permite administratorului să șteargă un locatar din sistem
@app.route('/delete_tenant/<int:user_id>', methods=['POST'])
@login_required
def delete_tenant(user_id):
    return delete_tenant_from_block(user_id)

print("test")
if __name__ == '__main__':
    app.run(debug=True)