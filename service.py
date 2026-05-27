import hashlib
import re
from datetime import date

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def is_valid_email(email):
    return re.match(r'^[^@]+@[^@]+\.[^@]+$', email) is not None

def register_user(db, username, email, password):
    if not username or len(username) < 3:
        return {'success': False, 'error': 'Username must be at least 3 characters long.'}
    if not is_valid_email(email):
        return {'success': False, 'error': 'Invalid email address.'}
    if not password or len(password) < 6:
        return {'success': False, 'error': 'Password must be at least 6 characters long.'}

    if db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone():
        return {'success': False, 'error': 'This email is already registered.'}
    if db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone():
        return {'success': False, 'error': 'This username is already taken.'}

    db.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
               (username, email, hash_password(password)))
    db.commit()
    return {'success': True}

def login_user(db, email, password):
    if not email or not password:
        return {'success': False, 'error': 'Email and password are required.'}

    user = db.execute('SELECT * FROM users WHERE email = ? AND password_hash = ?',
                      (email, hash_password(password))).fetchone()
    if not user:
        return {'success': False, 'error': 'Incorrect email or password.'}

    return {'success': True, 'user': dict(user)}

def is_valid_year(year):
    try:
        y = int(year)
        return 1900 <= y <= date.today().year + 1
    except (ValueError, TypeError):
        return False

def is_positive_number(value):
    try:
        return float(value) >= 0
    except (ValueError, TypeError):
        return False

def get_vehicles_by_user(db, user_id):
    return db.execute(
        'SELECT * FROM vehicles WHERE user_id = ? ORDER BY created_at DESC',
        (user_id,)
    ).fetchall()

def add_vehicle(db, data):
    if not data['brand'] or not data['model']:
        return {'success': False, 'error': 'Brand and model are required.'}
    if not is_valid_year(data['year']):
        return {'success': False, 'error': 'Invalid year.'}
    if not data['plate']:
        return {'success': False, 'error': 'Plate number is required.'}
    if not is_positive_number(data['current_km']):
        return {'success': False, 'error': 'Invalid mileage value.'}
    if db.execute('SELECT id FROM vehicles WHERE plate = ? AND user_id = ?',
                  (data['plate'], data['user_id'])).fetchone():
        return {'success': False, 'error': 'A vehicle with this plate number already exists.'}

    db.execute('''INSERT INTO vehicles
                  (user_id, brand, model, year, plate, current_km, fuel_type, motor, color, notes)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
               (data['user_id'], data['brand'], data['model'], data['year'],
                data['plate'], data['current_km'], data['fuel_type'],
                data.get('motor', ''), data['color'], data['notes']))
    db.commit()
    return {'success': True}

def get_vehicle(db, vehicle_id, user_id):
    return db.execute(
        'SELECT * FROM vehicles WHERE id = ? AND user_id = ?',
        (vehicle_id, user_id)
    ).fetchone()

def get_maintenances(db, vehicle_id):
    return db.execute(
        'SELECT * FROM maintenances WHERE vehicle_id = ? ORDER BY date DESC',
        (vehicle_id,)
    ).fetchall()

def get_faults(db, vehicle_id):
    return db.execute(
        'SELECT * FROM faults WHERE vehicle_id = ? ORDER BY date_reported DESC',
        (vehicle_id,)
    ).fetchall()

def get_total_cost_by_vehicle(db, vehicle_id):
    m = db.execute('SELECT COALESCE(SUM(cost),0) as t FROM maintenances WHERE vehicle_id=?',
                   (vehicle_id,)).fetchone()['t']
    f = db.execute('SELECT COALESCE(SUM(repair_cost),0) as t FROM faults WHERE vehicle_id=?',
                   (vehicle_id,)).fetchone()['t']
    return round(m + f, 2)