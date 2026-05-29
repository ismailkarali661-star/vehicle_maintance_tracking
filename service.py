import hashlib
import re
from datetime import date, timedelta

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

def update_vehicle(db, vehicle_id, user_id, data):
    if not data['brand'] or not data['model']:
        return {'success': False, 'error': 'Brand and model are required.'}
    if not is_valid_year(data['year']):
        return {'success': False, 'error': 'Invalid year.'}
    db.execute('''UPDATE vehicles SET brand=?, model=?, year=?, plate=?, current_km=?,
                  fuel_type=?, motor=?, color=?, notes=? WHERE id=? AND user_id=?''',
               (data['brand'], data['model'], data['year'], data['plate'],
                data['current_km'], data['fuel_type'], data.get('motor', ''),
                data['color'], data['notes'], vehicle_id, user_id))
    db.commit()
    return {'success': True}

def delete_vehicle(db, vehicle_id, user_id):
    if not get_vehicle(db, vehicle_id, user_id):
        return {'success': False, 'error': 'Vehicle not found.'}
    db.execute('DELETE FROM maintenances WHERE vehicle_id = ?', (vehicle_id,))
    db.execute('DELETE FROM faults WHERE vehicle_id = ?', (vehicle_id,))
    db.execute('DELETE FROM vehicles WHERE id = ? AND user_id = ?', (vehicle_id, user_id))
    db.commit()
    return {'success': True}

def update_vehicle_km(db, vehicle_id, user_id, new_km):
    if not is_positive_number(new_km):
        return {'success': False, 'error': 'Invalid mileage value.'}
    db.execute('UPDATE vehicles SET current_km=? WHERE id=? AND user_id=?',
               (int(float(new_km)), vehicle_id, user_id))
    db.commit()
    return {'success': True}

def add_maintenance(db, data):
    if not data['maintenance_type']:
        return {'success': False, 'error': 'Maintenance type is required.'}
    if not data['date']:
        return {'success': False, 'error': 'Date is required.'}
    if not is_positive_number(data['km_at_service']):
        return {'success': False, 'error': 'Invalid mileage value.'}

    db.execute('''INSERT INTO maintenances
                  (vehicle_id, maintenance_type, date, km_at_service,
                   next_service_km, next_service_date, cost, service_provider, notes)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
               (data['vehicle_id'], data['maintenance_type'], data['date'],
                data['km_at_service'], data['next_service_km'], data['next_service_date'],
                data['cost'], data['service_provider'], data['notes']))

    db.execute('UPDATE vehicles SET current_km = ? WHERE id = ?',
               (int(float(data['km_at_service'])), data['vehicle_id']))

    db.commit()
    return {'success': True}

def get_maintenance(db, maintenance_id, vehicle_id):
    return db.execute('SELECT * FROM maintenances WHERE id = ? AND vehicle_id = ?',
                      (maintenance_id, vehicle_id)).fetchone()

def update_maintenance(db, maintenance_id, vehicle_id, data):
    if not data['maintenance_type']:
        return {'success': False, 'error': 'Maintenance type is required.'}
    if not data['date']:
        return {'success': False, 'error': 'Date is required.'}
    if not is_positive_number(data['km_at_service']):
        return {'success': False, 'error': 'Invalid mileage value.'}

    db.execute('''UPDATE maintenances SET maintenance_type=?, date=?, km_at_service=?,
                  next_service_km=?, next_service_date=?, cost=?, service_provider=?, notes=?
                  WHERE id=? AND vehicle_id=?''',
               (data['maintenance_type'], data['date'], data['km_at_service'],
                data['next_service_km'], data['next_service_date'], data['cost'],
                data['service_provider'], data['notes'], maintenance_id, vehicle_id))
    db.commit()
    return {'success': True}

def delete_maintenance(db, maintenance_id, vehicle_id):
    if not get_maintenance(db, maintenance_id, vehicle_id):
        return {'success': False, 'error': 'Maintenance record not found.'}

    db.execute('DELETE FROM maintenances WHERE id = ? AND vehicle_id = ?',
               (maintenance_id, vehicle_id))
    db.commit()
    return {'success': True}

def search_maintenances(db, user_id, query, vehicle_id=None):
    params = [user_id]
    sql = '''SELECT m.*, v.brand, v.model, v.plate
             FROM maintenances m JOIN vehicles v ON m.vehicle_id = v.id
             WHERE v.user_id = ?'''
    if query:
        sql += ' AND (m.maintenance_type LIKE ? OR m.notes LIKE ?)'
        params += [f'%{query}%', f'%{query}%']
    if vehicle_id:
        sql += ' AND m.vehicle_id = ?'
        params.append(vehicle_id)
    sql += ' ORDER BY m.date DESC'
    return db.execute(sql, params).fetchall()

def get_reminders(db, user_id):
    today = date.today().isoformat()
    future_date = (date.today() + timedelta(days=30)).isoformat()

    date_reminders = db.execute('''
        SELECT m.*, v.brand, v.model, v.plate, 'date' as reminder_type
        FROM maintenances m JOIN vehicles v ON m.vehicle_id = v.id
        WHERE v.user_id = ? AND m.next_service_date IS NOT NULL
          AND m.next_service_date BETWEEN ? AND ?
        ORDER BY m.next_service_date ASC
    ''', (user_id, today, future_date)).fetchall()

    overdue = db.execute('''
        SELECT m.*, v.brand, v.model, v.plate, 'overdue' as reminder_type
        FROM maintenances m JOIN vehicles v ON m.vehicle_id = v.id
        WHERE v.user_id = ?
          AND ((m.next_service_date IS NOT NULL AND m.next_service_date < ?)
           OR (m.next_service_km IS NOT NULL AND m.next_service_km < v.current_km))
        ORDER BY m.next_service_date ASC
    ''', (user_id, today)).fetchall()

    return {'date': date_reminders, 'overdue': overdue}


def add_fault(db, data):
    if not data['title']:
        return {'success': False, 'error': 'Title is required.'}
    if not data['date_reported']:
        return {'success': False, 'error': 'Date reported is required.'}

    db.execute('''INSERT INTO faults
                  (vehicle_id, title, description, category, km_at_fault,
                   date_reported, severity, status, repair_cost, resolved_date)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
               (data['vehicle_id'], data['title'], data['description'],
                data.get('category', 'other'), data.get('km_at_fault'),
                data['date_reported'], data['severity'],
                data.get('status', 'open'), data.get('repair_cost', 0),
                data.get('resolved_date')))
    db.commit()
    return {'success': True}