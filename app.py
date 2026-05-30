from flask import Flask, render_template, request, redirect, url_for, session, flash, g
import sqlite3
import os
import json
from datetime import date
from functools import wraps
from services import (
    register_user, login_user,
    get_vehicles_by_user, add_vehicle, get_vehicle, update_vehicle, delete_vehicle,
    add_maintenance, get_maintenances, get_maintenance, update_maintenance, delete_maintenance,
    add_fault, get_faults, get_fault, update_fault, delete_fault,
    get_total_cost_by_vehicle, search_maintenances,
    get_maintenance_advisor_analysis, update_vehicle_km,
)
from seed_knowledge import get_chronic_faults

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'vehicle_maintenance_secret_key_2024')
DATABASE = 'vehicle_maintenance.db'


# ─── DATABASE HELPERS ────────────────────────────────────────────────────────

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


def _catalog_data(db):
    rows = db.execute(
        'SELECT DISTINCT brand, model FROM vehicle_catalog ORDER BY brand, model'
    ).fetchall()
    brands, models = [], {}
    for row in rows:
        b, m = row['brand'], row['model']
        if b not in models:
            brands.append(b)
            models[b] = []
        if m not in models[b]:
            models[b].append(m)
    engines = {}
    for row in db.execute(
            'SELECT brand, model, engine, fuel_type FROM engine_variants ORDER BY brand, model, engine'
    ).fetchall():
        b, m, e, ft = row['brand'], row['model'], row['engine'], row['fuel_type']
        if b not in engines:
            engines[b] = {}
        if m not in engines[b]:
            engines[b][m] = []
        engines[b][m].append({'engine': e, 'fuel_type': ft})
    return brands, models, engines


def _open_fault_counts(db, user_id):
    rows = db.execute(
        '''SELECT f.vehicle_id, COUNT(*) as cnt FROM faults f
           JOIN vehicles v ON f.vehicle_id = v.id
           WHERE f.status = 'open' AND v.user_id = ?
           GROUP BY f.vehicle_id''',
        (user_id,)
    ).fetchall()
    return {r['vehicle_id']: r['cnt'] for r in rows}


def _migrate_db(db):
    """Add new columns to existing tables without losing data."""
    vcols = {r[1] for r in db.execute('PRAGMA table_info(vehicles)').fetchall()}
    if 'motor' not in vcols:
        db.execute('ALTER TABLE vehicles ADD COLUMN motor TEXT')
        db.commit()

    fcols = {r[1] for r in db.execute('PRAGMA table_info(faults)').fetchall()}
    if 'category' not in fcols:
        db.execute('ALTER TABLE faults ADD COLUMN category TEXT DEFAULT "other"')
        db.commit()
    if 'km_at_fault' not in fcols:
        db.execute('ALTER TABLE faults ADD COLUMN km_at_fault INTEGER')
        db.commit()

    tables = {r[0] for r in db.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    if 'engine_variants' not in tables:
        db.execute('''CREATE TABLE IF NOT EXISTS engine_variants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            engine TEXT NOT NULL,
            fuel_type TEXT NOT NULL
        )''')
        db.commit()
        from seed_knowledge import ENGINE_VARIANTS
        db.executemany(
            'INSERT INTO engine_variants (brand, model, engine, fuel_type) VALUES (?,?,?,?)',
            ENGINE_VARIANTS
        )
        db.commit()

    # Migrate purchase_guide_notes column names (price_min_tl -> price_min etc.)
    if 'purchase_guide_notes' in tables:
        pgcols = {r[1] for r in db.execute(
            'PRAGMA table_info(purchase_guide_notes)'
        ).fetchall()}
        if 'price_min_tl' in pgcols and 'price_min' not in pgcols:
            db.execute('ALTER TABLE purchase_guide_notes RENAME COLUMN price_min_tl TO price_min')
            db.commit()
        if 'price_max_tl' in pgcols and 'price_max' not in pgcols:
            db.execute('ALTER TABLE purchase_guide_notes RENAME COLUMN price_max_tl TO price_max')
            db.commit()


# ─── AUTH HELPERS ─────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Bu sayfaya erişmek için giriş yapmanız gerekiyor.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        from seed_knowledge import seed
        seed()


# ─── AUTH ─────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        if not username or not email or not password:
            flash('Tüm alanlar zorunludur.', 'danger')
            return render_template('register.html')
        db = get_db()
        result = register_user(db, username, email, password)
        if result['success']:
            flash('Kayıt başarılı! Şimdi giriş yapabilirsiniz.', 'success')
            return redirect(url_for('login'))
        flash(result['error'], 'danger')
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        if not email or not password:
            flash('E-posta ve şifre zorunludur.', 'danger')
            return render_template('login.html')
        db = get_db()
        result = login_user(db, email, password)
        if result['success']:
            session['user_id']  = result['user']['id']
            session['username'] = result['user']['username']
            flash(f'Hoş geldiniz, {result["user"]["username"]}!', 'success')
            return redirect(url_for('dashboard'))
        flash(result['error'], 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Başarıyla çıkış yaptınız.', 'info')
    return redirect(url_for('index'))


# ─── DASHBOARD ────────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    db      = get_db()
    user_id = session['user_id']
    vehicles = get_vehicles_by_user(db, user_id)
    costs    = {v['id']: get_total_cost_by_vehicle(db, v['id']) for v in vehicles}
    all_overdue, all_due = [], []
    for v in vehicles:
        analysis = get_maintenance_advisor_analysis(db, v['id'])
        if analysis:
            for item in analysis.get('overdue', []):
                all_overdue.append({**item, 'vehicle': v})
            for item in analysis.get('due', []):
                all_due.append({**item, 'vehicle': v})
    open_faults = _open_fault_counts(db, user_id)
    return render_template('dashboard.html',
                           vehicles=vehicles, costs=costs,
                           all_overdue=all_overdue, all_due=all_due,
                           open_faults=open_faults)


# ─── VEHICLES ─────────────────────────────────────────────────────────────────

@app.route('/vehicles')
@login_required
def vehicles():
    db = get_db()
    vehicle_list = get_vehicles_by_user(db, session['user_id'])
    open_faults  = _open_fault_counts(db, session['user_id'])
    return render_template('vehicles.html', vehicles=vehicle_list, open_faults=open_faults)


@app.route('/vehicles/add', methods=['GET', 'POST'])
@login_required
def add_vehicle_route():
    db = get_db()
    if request.method == 'POST':
        # Handle "other" brand/model manual entry
        brand = request.form.get('brand', '').strip()
        model = request.form.get('model', '').strip()
        if brand == '__other__':
            brand = request.form.get('brand_manual', '').strip()
        if model == '__other__':
            model = request.form.get('model_manual', '').strip()
        if not brand or not model:
            flash('Marka ve model zorunludur.', 'danger')
        else:
            data = {
                'user_id':    session['user_id'],
                'brand':      brand,
                'model':      model,
                'year':       request.form.get('year'),
                'plate':      request.form.get('plate', '').strip().upper(),
                'current_km': request.form.get('current_km'),
                'fuel_type':  request.form.get('fuel_type'),
                'motor':      request.form.get('motor', '').strip(),
                'color':      request.form.get('color', '').strip(),
                'notes':      request.form.get('notes', '').strip(),
            }
            result = add_vehicle(db, data)
            if result['success']:
                flash('Araç başarıyla eklendi.', 'success')
                return redirect(url_for('vehicles'))
            flash(result['error'], 'danger')
    brands, models, engines = _catalog_data(db)
    return render_template('vehicle_form.html', vehicle=None, action='add',
                           catalog_brands=brands, catalog_models=models,
                           engine_data=engines)


@app.route('/vehicles/<int:vehicle_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_vehicle_route(vehicle_id):
    db      = get_db()
    vehicle = get_vehicle(db, vehicle_id, session['user_id'])
    if not vehicle:
        flash('Araç bulunamadı.', 'danger')
        return redirect(url_for('vehicles'))
    if request.method == 'POST':
        brand = request.form.get('brand', '').strip()
        model = request.form.get('model', '').strip()
        if brand == '__other__':
            brand = request.form.get('brand_manual', '').strip()
        if model == '__other__':
            model = request.form.get('model_manual', '').strip()
        if not brand or not model:
            flash('Marka ve model zorunludur.', 'danger')
        else:
            data = {
                'brand':      brand,
                'model':      model,
                'year':       request.form.get('year'),
                'plate':      request.form.get('plate', '').strip().upper(),
                'current_km': request.form.get('current_km'),
                'fuel_type':  request.form.get('fuel_type'),
                'motor':      request.form.get('motor', '').strip(),
                'color':      request.form.get('color', '').strip(),
                'notes':      request.form.get('notes', '').strip(),
            }
            result = update_vehicle(db, vehicle_id, session['user_id'], data)
            if result['success']:
                flash('Araç bilgileri güncellendi.', 'success')
                return redirect(url_for('vehicles'))
            flash(result['error'], 'danger')
    brands, models, engines = _catalog_data(db)
    return render_template('vehicle_form.html', vehicle=vehicle, action='edit',
                           catalog_brands=brands, catalog_models=models,
                           engine_data=engines)


@app.route('/vehicles/<int:vehicle_id>/delete', methods=['POST'])
@login_required
def delete_vehicle_route(vehicle_id):
    db     = get_db()
    result = delete_vehicle(db, vehicle_id, session['user_id'])
    if result['success']:
        flash('Araç silindi.', 'success')
    else:
        flash(result['error'], 'danger')
    return redirect(url_for('vehicles'))


@app.route('/vehicles/<int:vehicle_id>/update-km', methods=['POST'])
@login_required
def update_vehicle_km_route(vehicle_id):
    new_km = request.form.get('current_km', '').strip()
    if not new_km:
        flash('Kilometre değeri zorunludur.', 'danger')
        return redirect(request.referrer or url_for('vehicles'))
    db     = get_db()
    result = update_vehicle_km(db, vehicle_id, session['user_id'], new_km)
    if result['success']:
        flash('Kilometre başarıyla güncellendi.', 'success')
    else:
        flash(result['error'], 'danger')
    return redirect(request.referrer or url_for('vehicles'))


@app.route('/vehicles/<int:vehicle_id>')
@login_required
def vehicle_detail(vehicle_id):
    db      = get_db()
    vehicle = get_vehicle(db, vehicle_id, session['user_id'])
    if not vehicle:
        flash('Vehicle not found.', 'danger')
        return redirect(url_for('vehicles'))
    maintenances = get_maintenances(db, vehicle_id)
    faults       = get_faults(db, vehicle_id)
    total_cost   = get_total_cost_by_vehicle(db, vehicle_id)
    return render_template('vehicle_detail.html', vehicle=vehicle,
                           maintenances=maintenances, faults=faults,
                           total_cost=total_cost)


# ─── MAINTENANCE ──────────────────────────────────────────────────────────────

@app.route('/vehicles/<int:vehicle_id>/maintenance/add', methods=['GET', 'POST'])
@login_required
def add_maintenance_route(vehicle_id):
    db      = get_db()
    vehicle = get_vehicle(db, vehicle_id, session['user_id'])
    if not vehicle:
        flash('Araç bulunamadı.', 'danger')
        return redirect(url_for('vehicles'))
    if request.method == 'POST':
        data = {
            'vehicle_id':        vehicle_id,
            'maintenance_type':  request.form.get('maintenance_type', '').strip(),
            'date':              request.form.get('date'),
            'km_at_service':     request.form.get('km_at_service'),
            'next_service_km':   request.form.get('next_service_km') or None,
            'next_service_date': request.form.get('next_service_date') or None,
            'cost':              request.form.get('cost') or 0,
            'service_provider':  request.form.get('service_provider', '').strip(),
            'notes':             request.form.get('notes', '').strip(),
        }
        if not data['maintenance_type'] or not data['date'] or not data['km_at_service']:
            flash('Bakım türü, tarih ve kilometre zorunludur.', 'danger')
        else:
            result = add_maintenance(db, data)
            if result['success']:
                flash('Bakım kaydı eklendi.', 'success')
                return redirect(url_for('vehicle_detail', vehicle_id=vehicle_id))
            flash(result['error'], 'danger')
    prefill_type = request.args.get('type', '')
    quick        = request.args.get('quick', '0') == '1'
    return render_template('maintenance_form.html', vehicle=vehicle,
                           maintenance=None, action='add',
                           prefill_type=prefill_type, quick=quick)


@app.route('/vehicles/<int:vehicle_id>/maintenance/<int:maintenance_id>/edit',
           methods=['GET', 'POST'])
@login_required
def edit_maintenance_route(vehicle_id, maintenance_id):
    db          = get_db()
    vehicle     = get_vehicle(db, vehicle_id, session['user_id'])
    if not vehicle:
        flash('Araç bulunamadı.', 'danger')
        return redirect(url_for('vehicles'))
    maintenance = get_maintenance(db, maintenance_id, vehicle_id)
    if not maintenance:
        flash('Bakım kaydı bulunamadı.', 'danger')
        return redirect(url_for('vehicle_detail', vehicle_id=vehicle_id))
    if request.method == 'POST':
        data = {
            'maintenance_type':  request.form.get('maintenance_type', '').strip(),
            'date':              request.form.get('date'),
            'km_at_service':     request.form.get('km_at_service'),
            'next_service_km':   request.form.get('next_service_km') or None,
            'next_service_date': request.form.get('next_service_date') or None,
            'cost':              request.form.get('cost') or 0,
            'service_provider':  request.form.get('service_provider', '').strip(),
            'notes':             request.form.get('notes', '').strip(),
        }
        if not data['maintenance_type'] or not data['date'] or not data['km_at_service']:
            flash('Bakım türü, tarih ve kilometre zorunludur.', 'danger')
        else:
            result = update_maintenance(db, maintenance_id, vehicle_id, data)
            if result['success']:
                flash('Bakım kaydı güncellendi.', 'success')
                return redirect(url_for('vehicle_detail', vehicle_id=vehicle_id))
            flash(result['error'], 'danger')
    return render_template('maintenance_form.html', vehicle=vehicle,
                           maintenance=maintenance, action='edit')


@app.route('/vehicles/<int:vehicle_id>/maintenance/<int:maintenance_id>/delete',
           methods=['POST'])
@login_required
def delete_maintenance_route(vehicle_id, maintenance_id):
    db      = get_db()
    vehicle = get_vehicle(db, vehicle_id, session['user_id'])
    if not vehicle:
        flash('Araç bulunamadı.', 'danger')
        return redirect(url_for('vehicles'))
    result = delete_maintenance(db, maintenance_id, vehicle_id)
    if result['success']:
        flash('Bakım kaydı silindi.', 'success')
    else:
        flash(result['error'], 'danger')
    return redirect(url_for('vehicle_detail', vehicle_id=vehicle_id))


@app.route('/maintenance/search')
@login_required
def search_maintenance_route():
    db         = get_db()
    query      = request.args.get('q', '').strip()
    vehicle_id = request.args.get('vehicle_id', '').strip() or None
    results    = search_maintenances(db, session['user_id'], query, vehicle_id)
    vehicle_list = get_vehicles_by_user(db, session['user_id'])

    selected_vehicle_obj = None
    chronic  = []
    analysis = None
    if vehicle_id:
        try:
            vid = int(vehicle_id)
        except ValueError:
            vid = None
        if vid:
            selected_vehicle_obj = get_vehicle(db, vid, session['user_id'])
            if selected_vehicle_obj:
                chronic  = get_chronic_faults(
                    selected_vehicle_obj['brand'],
                    selected_vehicle_obj['model'],
                    selected_vehicle_obj['year']
                )
                analysis = get_maintenance_advisor_analysis(db, vid)

    return render_template('maintenance_search.html',
                           results=results, query=query,
                           vehicles=vehicle_list,
                           selected_vehicle=vehicle_id,
                           selected_vehicle_obj=selected_vehicle_obj,
                           chronic_faults=chronic,
                           analysis=analysis)


# ─── FAULTS ───────────────────────────────────────────────────────────────────

@app.route('/vehicles/<int:vehicle_id>/faults/add', methods=['GET', 'POST'])
@login_required
def add_fault_route(vehicle_id):
    db      = get_db()
    vehicle = get_vehicle(db, vehicle_id, session['user_id'])
    if not vehicle:
        flash('Araç bulunamadı.', 'danger')
        return redirect(url_for('vehicles'))
    if request.method == 'POST':
        data = {
            'vehicle_id':    vehicle_id,
            'title':         request.form.get('title', '').strip(),
            'description':   request.form.get('description', '').strip(),
            'category':      request.form.get('category', 'other'),
            'km_at_fault':   request.form.get('km_at_fault') or None,
            'date_reported': request.form.get('date_reported'),
            'severity':      request.form.get('severity', 'medium'),
            'status':        request.form.get('status', 'open'),
            'repair_cost':   request.form.get('repair_cost') or 0,
            'resolved_date': request.form.get('resolved_date') or None,
        }
        if not data['title'] or not data['date_reported']:
            flash('Başlık ve tarih zorunludur.', 'danger')
        else:
            result = add_fault(db, data)
            if result['success']:
                flash('Arıza kaydı eklendi.', 'success')
                return redirect(url_for('vehicle_detail', vehicle_id=vehicle_id))
            flash(result['error'], 'danger')
    return render_template('fault_form.html', vehicle=vehicle, fault=None, action='add')


@app.route('/vehicles/<int:vehicle_id>/faults/<int:fault_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_fault_route(vehicle_id, fault_id):
    db      = get_db()
    vehicle = get_vehicle(db, vehicle_id, session['user_id'])
    if not vehicle:
        flash('Araç bulunamadı.', 'danger')
        return redirect(url_for('vehicles'))
    fault = get_fault(db, fault_id, vehicle_id)
    if not fault:
        flash('Arıza kaydı bulunamadı.', 'danger')
        return redirect(url_for('vehicle_detail', vehicle_id=vehicle_id))
    if request.method == 'POST':
        data = {
            'title':         request.form.get('title', '').strip(),
            'description':   request.form.get('description', '').strip(),
            'category':      request.form.get('category', 'other'),
            'km_at_fault':   request.form.get('km_at_fault') or None,
            'date_reported': request.form.get('date_reported'),
            'severity':      request.form.get('severity', 'medium'),
            'status':        request.form.get('status', 'open'),
            'repair_cost':   request.form.get('repair_cost') or 0,
            'resolved_date': request.form.get('resolved_date') or None,
        }
        if not data['title'] or not data['date_reported']:
            flash('Başlık ve tarih zorunludur.', 'danger')
        else:
            result = update_fault(db, fault_id, vehicle_id, data)
            if result['success']:
                flash('Arıza kaydı güncellendi.', 'success')
                return redirect(url_for('vehicle_detail', vehicle_id=vehicle_id))
            flash(result['error'], 'danger')
    return render_template('fault_form.html', vehicle=vehicle, fault=fault, action='edit')


@app.route('/vehicles/<int:vehicle_id>/faults/<int:fault_id>/resolve', methods=['POST'])
@login_required
def resolve_fault_route(vehicle_id, fault_id):
    db      = get_db()
    vehicle = get_vehicle(db, vehicle_id, session['user_id'])
    if not vehicle:
        flash('Vehicle not found.', 'danger')
        return redirect(url_for('vehicles'))
    db.execute(
        "UPDATE faults SET status='resolved', resolved_date=? WHERE id=? AND vehicle_id=?",
        (date.today().isoformat(), fault_id, vehicle_id)
    )
    db.commit()
    flash('Fault marked as resolved.', 'success')
    return redirect(url_for('vehicle_detail', vehicle_id=vehicle_id))


@app.route('/vehicles/<int:vehicle_id>/faults/<int:fault_id>/delete', methods=['POST'])
@login_required
def delete_fault_route(vehicle_id, fault_id):
    db      = get_db()
    vehicle = get_vehicle(db, vehicle_id, session['user_id'])
    if not vehicle:
        flash('Vehicle not found.', 'danger')
        return redirect(url_for('vehicles'))
    result = delete_fault(db, fault_id, vehicle_id)
    if result['success']:
        flash('Fault record deleted.', 'success')
    else:
        flash(result['error'], 'danger')
    return redirect(url_for('vehicle_detail', vehicle_id=vehicle_id))


# ─── ADVISOR ──────────────────────────────────────────────────────────────────

@app.route('/vehicles/<int:vehicle_id>/advisor')
@login_required
def vehicle_advisor(vehicle_id):
    db      = get_db()
    vehicle = get_vehicle(db, vehicle_id, session['user_id'])
    if not vehicle:
        flash('Vehicle not found.', 'danger')
        return redirect(url_for('vehicles'))
    analysis = get_maintenance_advisor_analysis(db, vehicle_id)
    return render_template('advisor.html', vehicle=vehicle, analysis=analysis)


# ─── BUYER GUIDE ──────────────────────────────────────────────────────────────

@app.route('/vehicle-buyer-guide')
@login_required
def vehicle_buyer_guide():
    db = get_db()
    brands, models, engines = _catalog_data(db)

    selected_brand = request.args.get('brand', '').strip()
    selected_model = request.args.get('model', '').strip()

    chronic_faults       = None
    maintenance_schedule = None
    guide_note           = None

    if selected_brand and selected_model:
        # 1. Production start year
        year_row  = db.execute(
            'SELECT year_from FROM vehicle_catalog WHERE brand=? AND model=? LIMIT 1',
            (selected_brand, selected_model)
        ).fetchone()
        prod_year = year_row['year_from'] if year_row else 2015

        # 2. Chronic issues
        chronic_faults = get_chronic_faults(selected_brand, selected_model, prod_year)

        # 3. Fuel type
        fuel_row  = db.execute(
            'SELECT fuel_type FROM vehicle_catalog WHERE brand=? AND model=? LIMIT 1',
            (selected_brand, selected_model)
        ).fetchone()
        fuel_type = fuel_row['fuel_type'] if fuel_row else 'petrol'

        # 4. Buyer guide notes
        gn_row = db.execute(
            'SELECT * FROM purchase_guide_notes WHERE brand=? AND model=? LIMIT 1',
            (selected_brand, selected_model)
        ).fetchone()
        if gn_row:
            guide_note = dict(gn_row)
            guide_note['pros'] = json.loads(guide_note.get('pros') or '[]')
            guide_note['cons'] = json.loads(guide_note.get('cons') or '[]')

        # 5. 200,000 km Maintenance Schedule
        maintenance_schedule = []
        standard_items = [
            'Engine Oil Change',
            'Oil Filter Replacement',
            'Air Filter Replacement',
            'Cabin Filter Replacement',
        ]
        if fuel_type == 'electric':
            standard_items = ['Cabin Filter Replacement', 'Brake Fluid Check']

        for km in range(15000, 200001, 15000):
            items = list(standard_items)
            if fuel_type != 'electric':
                if km % 30000 == 0:
                    items.append('Front Brake Pad Inspection / Replacement')
                if km % 60000 == 0:
                    if fuel_type in ('petrol', 'hybrid'):
                        items.append('Spark Plug Set Replacement')
                    elif fuel_type == 'diesel':
                        items.append('Diesel Fuel Filter Replacement')
                    items.append('Transmission Fluid Check / Change')
                if km % 90000 == 0:
                    items.append('Timing Belt / Chain Kit Replacement')
                if km % 120000 == 0:
                    items.append('Drive Belt Replacement & Coolant Flush')
            else:
                if km % 60000 == 0:
                    items.append('Brake Pad Replacement')
                if km % 75000 == 0:
                    items.append('Reducer / Differential Oil Change')
                if km % 105000 == 0:
                    items.append('Battery Coolant Replacement')

            maintenance_schedule.append({
                'km':           f'{km:,}',
                'service_items': items,
            })

    return render_template('buyer_guide.html',
                           catalog_brands=brands,
                           catalog_models=models,
                           selected_brand=selected_brand,
                           selected_model=selected_model,
                           chronic_faults=chronic_faults,
                           maintenance_schedule=maintenance_schedule,
                           guide_note=guide_note)


# ─── ERROR HANDLERS ───────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        if not os.path.exists(DATABASE):
            init_db()
        else:
            _migrate_db(get_db())
        from seed_knowledge import seed
        seed()
    app.run(debug=os.environ.get('FLASK_DEBUG', 'true').lower() == 'true')