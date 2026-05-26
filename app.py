import sqlite3
from flask import Flask, g

app = Flask(__name__)
app.secret_key = 'arac_bakim_secret_key_2024'

DATABASE = 'vehicle_maintenance.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        from seed_knowledge import seed
        seed()

@app.route('/')
def index():
    return "AutoTrack Database and Seed Mechanism Ready!"

if __name__ == '__main__':
    app.run(debug=True)