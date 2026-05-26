import sqlite3

DATABASE = 'vehicle_maintenance.db'

VEHICLE_CATALOG = [
    # (brand, model, year_from, year_to, fuel_type, category)
    ('Toyota', 'Corolla', 2013, 2019, 'benzin', 'sedan'),
    ('Toyota', 'Corolla', 2019, None, 'benzin', 'sedan'),
    ('Toyota', 'Corolla', 2019, None, 'hibrit', 'sedan'),

]

ENGINE_VARIANTS = [
    # (brand, model, engine, fuel_type)
    ('Toyota', 'Corolla', '1.6 benzin', 'benzin'),
    ('Toyota', 'Corolla', '1.8 Hibrit', 'hibrit'),

]

MAINTENANCE_TEMPLATES = [

    ('Gasoline', 'Engine Oil + Filter Change',
     'oil, motor oil, engine oil',
     10000, 12, 1500, 4000, 'critical',
     'The most critical maintenance for gasoline vehicles.'),

]

def seed():
    conn = sqlite3.connect(DATABASE)
    # Zaten kayıt varsa tekrar ekleme
    if conn.execute('SELECT COUNT(*) FROM vehicle_catalog').fetchone()[0] > 0:
        conn.close()
        return
    conn.executemany(
        'INSERT INTO vehicle_catalog (brand,model,year_from,year_to,fuel_type,category) VALUES (?,?,?,?,?,?)',
        VEHICLE_CATALOG
    )
    conn.executemany(
        'INSERT INTO engine_variants (brand,model,engine,fuel_type) VALUES (?,?,?,?)',
        ENGINE_VARIANTS
    )

    conn.execute('''CREATE TABLE IF NOT EXISTS maintenance_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fuel_type TEXT,
        maintenance_type TEXT NOT NULL,
        keywords TEXT,
        interval_km INTEGER,
        interval_months INTEGER,
        cost_min_tl REAL,
        cost_max_tl REAL,
        priority TEXT DEFAULT 'routine',
        notes TEXT
    )''')
    conn.executemany(
        '''INSERT INTO maintenance_templates
           (fuel_type,maintenance_type,keywords,interval_km,interval_months,
            cost_min_tl,cost_max_tl,priority,notes) VALUES (?,?,?,?,?,?,?,?,?)''',
        MAINTENANCE_TEMPLATES
    )
    conn.commit()
    conn.close()

if __name__ == '__main__':
    seed()
    print('Seed comlated.')