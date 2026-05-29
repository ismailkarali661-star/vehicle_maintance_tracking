import sqlite3
from functools import wraps
from flask import Flask, g, session, flash, redirect, url_for, render_template, request
from services import (
    register_user, login_user, get_vehicles_by_user, add_vehicle,
    get_vehicle, get_maintenances, get_faults, get_total_cost_by_vehicle,
    update_vehicle_km
)

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
        b, m, e, ft = row['brand'], row['model'], row['engine'], row['fuel_type']
        if b not in engines: engines[b] = {}
        if m not in engines[b]: engines[b][m] = []
        engines[b][m].append({'engine': e, 'fuel_type': ft})
    return brands, models, engines

def _open_fault_counts(db, user_id):
    rows = db.execute('''
        SELECT f.vehicle_id, COUNT(*) as cnt FROM faults f
        JOIN vehicles v ON f.vehicle_id = v.id
        WHERE f.status = 'open' AND v.user_id = ?
        GROUP BY f.vehicle_id''', (user_id,)).fetchall()
    return {r['vehicle_id']: r['cnt'] for r in rows}

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        result = register_user(get_db(),
                               request.form['username'].strip(),
                               request.form['email'].strip(),
                               request.form['password'])
        if result['success']:
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        flash(result['error'], 'danger')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        result = login_user(get_db(),
                            request.form['email'].strip(),
                            request.form['password'])
        if result['success']:
            session['user_id'] = result['user']['id']
            session['username'] = result['user']['username']
            flash(f'Welcome, {result["user"]["username"]}!', 'success')
            return redirect(url_for('dashboard'))
        flash(result['error'], 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been successfully logged out.', 'info')
    return redirect(url_for('index'))

# Güncellenen rota
@app.route('/vehicles')
@login_required
def vehicles():
    db = get_db()
    vehicle_list = get_vehicles_by_user(db, session['user_id'])
    open_faults = _open_fault_counts(db, session['user_id'])
    return render_template('vehicles.html', vehicles=vehicle_list, open_faults=open_faults)

@app.route('/vehicles/add', methods=['GET', 'POST'])
@login_required
def add_vehicle_route():
    if request.method == 'POST':
        data = {
            'user_id': session['user_id'],
            'brand': request.form['brand'].strip(),
            'model': request.form['model'].strip(),
            'year': request.form['year'],
            'plate': request.form['plate'].strip().upper(),
            'current_km': request.form['current_km'],
            'fuel_type': request.form['fuel_type'],
            'motor': request.form.get('motor', '').strip(),
            'color': request.form.get('color', '').strip(),
            'notes': request.form.get('notes', '').strip(),
        }
        result = add_vehicle(get_db(), data)
        if result['success']:
            flash('Vehicle added successfully.', 'success')
            return redirect(url_for('vehicles'))
        flash(result['error'], 'danger')
    brands, models, engines = _catalog_data(get_db())
    return render_template('vehicle_form.html', vehicle=None, action='add',
                           catalog_brands=brands, catalog_models=models, engine_data=engines)

@app.route('/vehicles/<int:vehicle_id>')
@login_required
def vehicle_detail(vehicle_id):
    db = get_db()
    vehicle = get_vehicle(db, vehicle_id, session['user_id'])
    if not vehicle:
        flash('Vehicle not found.', 'danger')
        return redirect(url_for('vehicles'))
    return render_template('vehicle_detail.html',
                           vehicle=vehicle,
                           maintenances=get_maintenances(db, vehicle_id),
                           faults=get_faults(db, vehicle_id),
                           total_cost=get_total_cost_by_vehicle(db, vehicle_id))

@app.route('/vehicles/<int:vehicle_id>/update-km', methods=['POST'])
@login_required
def update_vehicle_km_route(vehicle_id):
    result = update_vehicle_km(get_db(), vehicle_id, session['user_id'],
                               request.form.get('current_km', '').strip())
    flash('Mileage updated successfully.' if result['success'] else result['error'],
          'success' if result['success'] else 'danger')
    return redirect(request.referrer or url_for('vehicles'))

if __name__ == '__main__':
    app.run(debug=True)