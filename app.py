import sqlite3
from functools import wraps
from flask import Flask, g, session, flash, redirect, url_for, render_template, request
from services import register_user, login_user, get_vehicles_by_user, add_vehicle

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

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def _catalog_data(db):
    rows = db.execute('SELECT DISTINCT brand, model FROM vehicle_catalog ORDER BY brand, model').fetchall()
    brands, models = [], {}
    for row in rows:
        b, m = row['brand'], row['model']
        if b not in models:
            brands.append(b)
            models[b] = []
        if m not in models[b]:
            models[b].append(m)
    engines = {}
    for row in db.execute('SELECT brand, model, engine, fuel_type FROM engine_variants').fetchall():
        b, m, e, ft = row['brand'], row['model'], row