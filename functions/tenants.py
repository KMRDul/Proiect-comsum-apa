from flask import redirect, url_for, request
from functions.database import add_user, delete_user

# Funcție pentru adăugarea unui locatar în bloc
def add_tenant_to_block(block_id):
    try:
        # Obținem datele locatarului din formular
        apartment = request.form['apartment']  # Numărul apartamentului
        name = request.form['name']  # Numele locatarului
        amount_due = 100  # Suma implicită de plată (100 lei)
        
        # Adăugăm locatarul în baza de date
        add_user(name, apartment, amount_due, block_id)
        
        # Redirecționăm către pagina de detalii a blocului
        return redirect(url_for('block_detail', block_id=block_id))
    except Exception as e:
        # Logăm și afișăm orice eroare apărută la adăugarea locatarului
        print(f"Eroare la adăugare locatar: {e}")
        return 'A apărut o eroare la adăugarea locatarului.', 500

# Funcție pentru ștergerea unui locatar
def delete_tenant_from_block(user_id):
    # Ștergem locatarul cu ID-ul specificat
    delete_user(user_id)
    
    # Redirecționăm înapoi la pagina de unde a venit cererea sau la pagina principală
    return redirect(request.referrer or url_for('index'))
