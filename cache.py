from flask_caching import Cache

# Adaugarea cache-ului pentru a rulare mai rapida a aplicatiei
cache = Cache(config={'CACHE_TYPE': 'simple'})