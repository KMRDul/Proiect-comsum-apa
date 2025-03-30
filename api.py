# import requests
# import random
#
# def fetch_users():
#     try:
#         response = requests.get("https://jsonplaceholder.typicode.com/users")
#         response.raise_for_status()  # Verifică dacă cererea a avut succes
#         data = response.json()
#         # Selectează numele utilizatorilor și generează o sumă aleatorie
#         user_data = [(user['id'], user['name'], random.uniform(50, 150)) for user in data]  # Obține ID, nume și suma aleatorie
#         return user_data
#     except requests.exceptions.RequestException as e:
#         print(f"Eroare la obținerea utilizatorilor: {e}")
#         return []  # Returnează o listă goală în caz de eroare