import sqlite3

DATABASE = 'vehicle_maintenance.db'

VEHICLE_CATALOG = [
    # (brand, model, year_from, year_to, fuel_type, category)
    ('Toyota', 'Corolla', 2013, 2019, 'Gasoline', 'sedan'),
    ('Toyota', 'Corolla', 2019, None, 'Gasoline', 'sedan'),
    ('Toyota', 'Corolla', 2019, None, 'Hybrid', 'sedan'),
]

ENGINE_VARIANTS = [
    # (brand, model, engine, fuel_type)
    ('Toyota', 'Corolla', '1.6 Gasoline', 'Gasoline'),
    ('Toyota', 'Corolla', '1.8 Hybrid', 'Hybrid'),
]

MAINTENANCE_TEMPLATES = [
    # (fuel_type, maintenance_type, keywords, interval_km, interval_months, cost_min_tl, cost_max_tl, priority, notes)
    ('Gasoline', 'Engine Oil + Filter Change',
     'oil, motor oil, engine oil',
     10000, 12, 1500, 4000, 'critical',
     'The most critical maintenance for gasoline vehicles.'),
]


CHRONIC_FAULTS = {
    ('Toyota', 'Corolla'): [
        {
            'title': 'Engine Oil Consumption',
            'description': 'High oil consumption is a common reported issue in 2013-2017 1.6 gasoline engines.',
            'severity': 'medium'
        },
        {
            'title': 'EGR Valve Clogging',
            'description': 'EGR valve clogging and efficiency issues can occur in hybrid or diesel variants over time.',
            'severity': 'low'
        },
    ],
    # Other models can be added here...
}

def get_chronic_faults(brand, model, year_from=None):
    return CHRONIC_FAULTS.get((brand, model), [])

def seed():
    conn = sqlite3.connect(DATABASE)


    conn.execute('''CREATE TABLE IF NOT EXISTS vehicle_catalog (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand TEXT NOT NULL,
        model TEXT NOT NULL,
        year_from INTEGER,
        year_to INTEGER,
        fuel_type TEXT,
        category TEXT
    )''')

    conn.execute('''CREATE TABLE IF NOT EXISTS engine_variants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand TEXT NOT NULL,
        model TEXT NOT NULL,
        engine TEXT NOT NULL,
        fuel_type TEXT NOT NULL
    )''')

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


    conn.execute('''CREATE TABLE IF NOT EXISTS chronic_fault_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand TEXT NOT NULL,
        model TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        severity TEXT DEFAULT 'low'
    )''')


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
    conn.executemany(
        '''INSERT INTO maintenance_templates
           (fuel_type,maintenance_type,keywords,interval_km,interval_months,
            cost_min_tl,cost_max_tl,priority,notes) VALUES (?,?,?,?,?,?,?,?,?)''',
        MAINTENANCE_TEMPLATES
    )

    chronic_insert_data = []
    for (brand, model), faults in CHRONIC_FAULTS.items():
        for f in faults:
            chronic_insert_data.append((brand, model, f['title'], f['description'], f['severity']))

    conn.executemany(
        '''INSERT INTO chronic_fault_templates (brand, model, title, description, severity) 
           VALUES (?, ?, ?, ?, ?)''',
        chronic_insert_data
    )

    conn.commit()
    conn.close()

if __name__ == '__main__':
    seed()
    print('Seed completed.')