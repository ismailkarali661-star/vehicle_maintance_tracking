import hashlib
import re
from datetime import date, timedelta


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def is_valid_email(email):
    return re.match(r'^[^@]+@[^@]+\.[^@]+$', email) is not None


def is_valid_plate(plate):
    """Turkish plate format: 34 ABC 123 or 34 AB 1234"""
    plate = plate.replace(' ', '').upper()
    return re.match(r'^[0-9]{2}[A-Z]{1,3}[0-9]{2,4}$', plate) is not None


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


# ─── AUTH ─────────────────────────────────────────────────────────────────────

def register_user(db, username, email, password):
    """Register a new user. Returns {'success': True} or {'success': False, 'error': '...'}"""
    if not username or len(username) < 3:
        return {'success': False, 'error': 'Kullanıcı adı en az 3 karakter olmalıdır.'}
    if not is_valid_email(email):
        return {'success': False, 'error': 'Geçersiz e-posta adresi.'}
    if not password or len(password) < 6:
        return {'success': False, 'error': 'Şifre en az 6 karakter olmalıdır.'}

    existing = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
    if existing:
        return {'success': False, 'error': 'Bu e-posta adresi zaten kayıtlı.'}

    existing_username = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    if existing_username:
        return {'success': False, 'error': 'Bu kullanıcı adı zaten alınmış.'}

    hashed = hash_password(password)
    db.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
               (username, email, hashed))
    db.commit()
    return {'success': True}


def login_user(db, email, password):
    """Authenticate a user. Returns {'success': True, 'user': {...}} or error."""
    if not email or not password:
        return {'success': False, 'error': 'E-posta ve şifre zorunludur.'}

    hashed = hash_password(password)
    user = db.execute('SELECT * FROM users WHERE email = ? AND password_hash = ?',
                      (email, hashed)).fetchone()
    if not user:
        return {'success': False, 'error': 'E-posta veya şifre hatalı.'}

    return {'success': True, 'user': dict(user)}


# ─── VEHICLES ────────────────────────────────────────────────────────────────

def get_vehicles_by_user(db, user_id):
    return db.execute('SELECT * FROM vehicles WHERE user_id = ? ORDER BY created_at DESC',
                      (user_id,)).fetchall()


def get_vehicle(db, vehicle_id, user_id):
    """Get a vehicle only if it belongs to the given user (ownership check)."""
    return db.execute('SELECT * FROM vehicles WHERE id = ? AND user_id = ?',
                      (vehicle_id, user_id)).fetchone()


def add_vehicle(db, data):
    """Add a new vehicle with validation."""
    if not data['brand'] or not data['model']:
        return {'success': False, 'error': 'Marka ve model zorunludur.'}
    if not is_valid_year(data['year']):
        return {'success': False, 'error': 'Geçersiz yıl.'}
    if not data['plate']:
        return {'success': False, 'error': 'Plaka zorunludur.'}
    if not is_positive_number(data.get('current_km', 0)):
        return {'success': False, 'error': 'Geçersiz km değeri.'}

    fuel_type = data.get('fuel_type') or 'benzin'

    existing = db.execute('SELECT id FROM vehicles WHERE plate = ?',
                          (data['plate'],)).fetchone()
    if existing:
        return {'success': False, 'error': 'Bu plaka sisteme zaten kayıtlı.'}

    db.execute('''INSERT INTO vehicles (user_id, brand, model, year, plate, current_km, fuel_type, motor, color, notes)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
               (data['user_id'], data['brand'], data['model'], data['year'],
                data['plate'], data.get('current_km', 0), fuel_type,
                data.get('motor', ''), data.get('color', ''), data.get('notes', '')))
    db.commit()
    return {'success': True}


def update_vehicle(db, vehicle_id, user_id, data):
    """Update a vehicle. Validates ownership implicitly via get_vehicle."""
    if not data['brand'] or not data['model']:
        return {'success': False, 'error': 'Marka ve model zorunludur.'}
    if not is_valid_year(data['year']):
        return {'success': False, 'error': 'Geçersiz yıl.'}
    if not is_positive_number(data.get('current_km', 0)):
        return {'success': False, 'error': 'Geçersiz km değeri.'}

    fuel_type = data.get('fuel_type') or 'benzin'

    db.execute('''UPDATE vehicles SET brand=?, model=?, year=?, plate=?, current_km=?,
                  fuel_type=?, motor=?, color=?, notes=? WHERE id=? AND user_id=?''',
               (data['brand'], data['model'], data['year'], data['plate'],
                data.get('current_km', 0), fuel_type, data.get('motor', ''),
                data.get('color', ''), data.get('notes', ''), vehicle_id, user_id))
    db.commit()
    return {'success': True}


def delete_vehicle(db, vehicle_id, user_id):
    """Delete a vehicle and all related records."""
    vehicle = get_vehicle(db, vehicle_id, user_id)
    if not vehicle:
        return {'success': False, 'error': 'Araç bulunamadı.'}
    db.execute('DELETE FROM maintenances WHERE vehicle_id = ?', (vehicle_id,))
    db.execute('DELETE FROM faults WHERE vehicle_id = ?', (vehicle_id,))
    db.execute('DELETE FROM vehicles WHERE id = ? AND user_id = ?', (vehicle_id, user_id))
    db.commit()
    return {'success': True}


# ─── MAINTENANCE ─────────────────────────────────────────────────────────────

def get_maintenances(db, vehicle_id):
    return db.execute('''SELECT * FROM maintenances WHERE vehicle_id = ?
                         ORDER BY date DESC''', (vehicle_id,)).fetchall()


def get_maintenance(db, maintenance_id, vehicle_id):
    return db.execute('SELECT * FROM maintenances WHERE id = ? AND vehicle_id = ?',
                      (maintenance_id, vehicle_id)).fetchone()


def add_maintenance(db, data):
    """Add a maintenance record with validation."""
    if not data['maintenance_type']:
        return {'success': False, 'error': 'Bakım türü zorunludur.'}
    if not data['date']:
        return {'success': False, 'error': 'Tarih zorunludur.'}
    if not is_positive_number(data['km_at_service']):
        return {'success': False, 'error': 'Geçersiz km değeri.'}
    if data['cost'] and not is_positive_number(data['cost']):
        return {'success': False, 'error': 'Geçersiz maliyet değeri.'}

    db.execute('''INSERT INTO maintenances
                  (vehicle_id, maintenance_type, date, km_at_service, next_service_km,
                   next_service_date, cost, service_provider, notes)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
               (data['vehicle_id'], data['maintenance_type'], data['date'],
                data['km_at_service'], data['next_service_km'], data['next_service_date'],
                data['cost'], data['service_provider'], data['notes']))
    db.commit()
    return {'success': True}


def update_maintenance(db, maintenance_id, vehicle_id, data):
    if not data['maintenance_type']:
        return {'success': False, 'error': 'Bakım türü zorunludur.'}
    if not is_positive_number(data['km_at_service']):
        return {'success': False, 'error': 'Geçersiz km değeri.'}

    db.execute('''UPDATE maintenances SET maintenance_type=?, date=?, km_at_service=?,
                  next_service_km=?, next_service_date=?, cost=?, service_provider=?, notes=?
                  WHERE id=? AND vehicle_id=?''',
               (data['maintenance_type'], data['date'], data['km_at_service'],
                data['next_service_km'], data['next_service_date'], data['cost'],
                data['service_provider'], data['notes'], maintenance_id, vehicle_id))
    db.commit()
    return {'success': True}


def delete_maintenance(db, maintenance_id, vehicle_id):
    maintenance = get_maintenance(db, maintenance_id, vehicle_id)
    if not maintenance:
        return {'success': False, 'error': 'Bakım kaydı bulunamadı.'}
    db.execute('DELETE FROM maintenances WHERE id = ? AND vehicle_id = ?',
               (maintenance_id, vehicle_id))
    db.commit()
    return {'success': True}


def search_maintenances(db, user_id, query, vehicle_id=None):
    """Search maintenances by type, provider, or notes."""
    sql = '''SELECT m.*, v.brand, v.model, v.plate FROM maintenances m
             JOIN vehicles v ON m.vehicle_id = v.id
             WHERE v.user_id = ?'''
    params = [user_id]
    if query:
        sql += ' AND (m.maintenance_type LIKE ? OR m.service_provider LIKE ? OR m.notes LIKE ?)'
        like = f'%{query}%'
        params += [like, like, like]
    if vehicle_id:
        sql += ' AND m.vehicle_id = ?'
        params.append(vehicle_id)
    sql += ' ORDER BY m.date DESC'
    return db.execute(sql, params).fetchall()


# ─── FAULTS ──────────────────────────────────────────────────────────────────

def get_faults(db, vehicle_id):
    return db.execute('SELECT * FROM faults WHERE vehicle_id = ? ORDER BY date_reported DESC',
                      (vehicle_id,)).fetchall()


def get_fault(db, fault_id, vehicle_id):
    return db.execute('SELECT * FROM faults WHERE id = ? AND vehicle_id = ?',
                      (fault_id, vehicle_id)).fetchone()


def add_fault(db, data):
    if not data['title']:
        return {'success': False, 'error': 'Arıza başlığı zorunludur.'}
    if not data['date_reported']:
        return {'success': False, 'error': 'Tarih zorunludur.'}
    if data['repair_cost'] and not is_positive_number(data['repair_cost']):
        return {'success': False, 'error': 'Geçersiz maliyet değeri.'}

    db.execute('''INSERT INTO faults
                  (vehicle_id, title, description, category, km_at_fault,
                   date_reported, severity, status, repair_cost, resolved_date)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
               (data['vehicle_id'], data['title'], data['description'],
                data.get('category', 'diger'), data.get('km_at_fault'),
                data['date_reported'], data['severity'], data['status'],
                data['repair_cost'], data['resolved_date']))
    db.commit()
    return {'success': True}


def update_fault(db, fault_id, vehicle_id, data):
    if not data['title']:
        return {'success': False, 'error': 'Arıza başlığı zorunludur.'}

    db.execute('''UPDATE faults SET title=?, description=?, category=?, km_at_fault=?,
                  date_reported=?, severity=?, status=?, repair_cost=?, resolved_date=?
                  WHERE id=? AND vehicle_id=?''',
               (data['title'], data['description'],
                data.get('category', 'diger'), data.get('km_at_fault'),
                data['date_reported'], data['severity'], data['status'],
                data['repair_cost'], data['resolved_date'], fault_id, vehicle_id))
    db.commit()
    return {'success': True}


def delete_fault(db, fault_id, vehicle_id):
    fault = get_fault(db, fault_id, vehicle_id)
    if not fault:
        return {'success': False, 'error': 'Arıza kaydı bulunamadı.'}
    db.execute('DELETE FROM faults WHERE id = ? AND vehicle_id = ?', (fault_id, vehicle_id))
    db.commit()
    return {'success': True}


# ─── REMINDERS & STATS ───────────────────────────────────────────────────────

def get_upcoming_reminders(db, user_id, days_ahead=30):
    future_date = (date.today() + timedelta(days=days_ahead)).isoformat()
    today = date.today().isoformat()

    date_reminders = db.execute('''
        SELECT m.*, v.brand, v.model, v.plate, v.current_km, 'date' as reminder_type
        FROM maintenances m
        JOIN vehicles v ON m.vehicle_id = v.id
        WHERE v.user_id = ?
          AND m.next_service_date IS NOT NULL
          AND m.next_service_date <= ?
          AND m.next_service_date >= ?
        ORDER BY m.next_service_date ASC
    ''', (user_id, future_date, today)).fetchall()

    km_reminders = db.execute('''
        SELECT m.*, v.brand, v.model, v.plate, v.current_km, 'km' as reminder_type
        FROM maintenances m
        JOIN vehicles v ON m.vehicle_id = v.id
        WHERE v.user_id = ?
          AND m.next_service_km IS NOT NULL
          AND m.next_service_km <= (v.current_km + 1000)
          AND m.next_service_km >= v.current_km
        ORDER BY m.next_service_km ASC
    ''', (user_id,)).fetchall()

    overdue = db.execute('''
        SELECT m.*, v.brand, v.model, v.plate, v.current_km, 'overdue' as reminder_type
        FROM maintenances m
        JOIN vehicles v ON m.vehicle_id = v.id
        WHERE v.user_id = ?
          AND (
            (m.next_service_date IS NOT NULL AND m.next_service_date < ?)
            OR (m.next_service_km IS NOT NULL AND m.next_service_km < v.current_km)
          )
        ORDER BY m.next_service_date ASC
    ''', (user_id, today)).fetchall()

    return {'date': date_reminders, 'km': km_reminders, 'overdue': overdue}


def get_total_cost_by_vehicle(db, vehicle_id):
    """Calculate total maintenance + repair cost for a vehicle."""
    maintenance_cost = db.execute(
        'SELECT COALESCE(SUM(cost), 0) as total FROM maintenances WHERE vehicle_id = ?',
        (vehicle_id,)
    ).fetchone()['total']

    fault_cost = db.execute(
        'SELECT COALESCE(SUM(repair_cost), 0) as total FROM faults WHERE vehicle_id = ?',
        (vehicle_id,)
    ).fetchone()['total']

    return round(maintenance_cost + fault_cost, 2)


def update_vehicle_km(db, vehicle_id, user_id, new_km):
    """Update a vehicle's current km. Returns success/error dict."""
    if not is_positive_number(new_km):
        return {'success': False, 'error': 'Geçersiz km değeri.'}
    db.execute(
        'UPDATE vehicles SET current_km=? WHERE id=? AND user_id=?',
        (int(float(new_km)), vehicle_id, user_id)
    )
    db.commit()
    return {'success': True}


# ─── ADVISOR ─────────────────────────────────────────────────────────────────

def _engine_category(motor):
    """Classify engine as 'small', 'medium', or 'large' based on motor description."""
    if not motor:
        return 'medium'
    s = motor.lower().replace(' ', '')
    large = ['v6', 'v8', 'v10', 'v12', '2.5', '2.7', '2.8', '2.9', '3.0', '3.5', '4.0', '4.2', '5.0', '6.2']
    small = ['1.0', '1.1', '1.2', '1.3', '1.4', '900cc', '1000', '1100', '1200', '1300', '1400']
    if any(m in s for m in large):
        return 'large'
    if any(m in s for m in small):
        return 'small'
    return 'medium'


def get_vehicle_catalog_match(db, brand, model, year, fuel_type):
    """Find best matching vehicle in catalog: exact → ignore year → ignore fuel_type."""
    row = db.execute(
        '''SELECT * FROM vehicle_catalog
           WHERE brand=? AND model=? AND fuel_type=?
             AND year_from<=? AND (year_to IS NULL OR year_to>=?)''',
        (brand, model, fuel_type, year, year)
    ).fetchone()
    if row:
        return row
    row = db.execute(
        'SELECT * FROM vehicle_catalog WHERE brand=? AND model=? AND fuel_type=?',
        (brand, model, fuel_type)
    ).fetchone()
    if row:
        return row
    return db.execute(
        'SELECT * FROM vehicle_catalog WHERE brand=? AND model=?',
        (brand, model)
    ).fetchone()


def _match_keywords(maintenance_type_text, keywords_csv):
    """Return True if any keyword in the CSV appears in the maintenance text."""
    text = maintenance_type_text.lower()
    for kw in keywords_csv.split(','):
        if kw.strip().lower() in text:
            return True
    return False


def get_maintenance_advisor_analysis(db, vehicle_id):
    """Compare maintenance history against templates and return categorized items."""
    vehicle = db.execute('SELECT * FROM vehicles WHERE id=?', (vehicle_id,)).fetchone()
    if not vehicle:
        return None

    current_km = vehicle['current_km']
    fuel_type = vehicle['fuel_type']
    try:
        motor = vehicle['motor'] or ''
    except (IndexError, KeyError):
        motor = ''
    engine_cat = _engine_category(motor)

    history = db.execute(
        'SELECT * FROM maintenances WHERE vehicle_id=? ORDER BY km_at_service DESC',
        (vehicle_id,)
    ).fetchall()

    templates = db.execute(
        'SELECT * FROM maintenance_templates WHERE fuel_type IS NULL OR fuel_type=?',
        (fuel_type,)
    ).fetchall()

    catalog = get_vehicle_catalog_match(
        db, vehicle['brand'], vehicle['model'], vehicle['year'], fuel_type
    )

    overdue, due, upcoming, good = [], [], [], []

    for tmpl in templates:
        last_entry = next(
            (h for h in history if _match_keywords(h['maintenance_type'], tmpl['keywords'])),
            None
        )

        last_km = last_entry['km_at_service'] if last_entry else None
        last_date = last_entry['date'] if last_entry else None
        interval_km = tmpl['interval_km']

        # Adjust engine oil change interval based on engine size
        interval_adjusted = False
        if interval_km and 'motor yağ' in (tmpl['keywords'] or '').lower():
            if engine_cat == 'large':
                new_interval = min(interval_km, 7500)
            elif engine_cat == 'small':
                new_interval = max(interval_km, 15000)
            else:
                new_interval = interval_km
            if new_interval != interval_km:
                interval_adjusted = True
                interval_km = new_interval

        next_km = None
        if interval_km:
            next_km = (last_km if last_km is not None else 0) + interval_km

        km_remaining = (next_km - current_km) if next_km is not None else None

        item = {
            'maintenance_type': tmpl['maintenance_type'],
            'priority': tmpl['priority'],
            'interval_km': interval_km,
            'interval_adjusted': interval_adjusted,
            'interval_months': tmpl['interval_months'],
            'last_km': last_km,
            'last_date': last_date,
            'next_km': next_km,
            'km_remaining': km_remaining,
            'cost_min': tmpl['cost_min_tl'],
            'cost_max': tmpl['cost_max_tl'],
            'notes': tmpl['notes'],
        }

        if km_remaining is None:
            good.append(item)
        elif km_remaining <= 0:
            overdue.append(item)
        elif km_remaining <= 1000:
            due.append(item)
        elif km_remaining <= 5000:
            upcoming.append(item)
        else:
            good.append(item)

    urgent = overdue + due
    return {
        'vehicle': vehicle,
        'catalog': catalog,
        'motor': motor,
        'engine_cat': engine_cat,
        'overdue': overdue,
        'due': due,
        'upcoming': upcoming,
        'good': good,
        'urgent_cost_min': sum(i['cost_min'] or 0 for i in urgent),
        'urgent_cost_max': sum(i['cost_max'] or 0 for i in urgent),
        'total_items': len(overdue) + len(due) + len(upcoming) + len(good),
    }