"""
Unit tests for services.py business logic.
Run with: python -m pytest test_services.py -v
"""

import sqlite3
import unittest
from services import (
    hash_password,
    is_valid_email,
    is_valid_plate,
    is_valid_year,
    is_positive_number,
    register_user,
    login_user,
    add_vehicle,
    update_vehicle,
    delete_vehicle,
    add_maintenance,
    add_fault,
    get_total_cost_by_vehicle,
    update_vehicle_km,
)


# ─── Test DB Setup ────────────────────────────────────────────────────────────

def create_test_db():
    """Create an in-memory SQLite database for testing."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.executescript('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            year INTEGER NOT NULL,
            plate TEXT NOT NULL,
            current_km INTEGER NOT NULL DEFAULT 0,
            fuel_type TEXT NOT NULL DEFAULT 'benzin',
            motor TEXT,
            color TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE maintenances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            maintenance_type TEXT NOT NULL,
            date TEXT NOT NULL,
            km_at_service INTEGER NOT NULL,
            next_service_km INTEGER,
            next_service_date TEXT,
            cost REAL DEFAULT 0,
            service_provider TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
        );
        CREATE TABLE faults (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL DEFAULT 'diger',
            km_at_fault INTEGER,
            date_reported TEXT NOT NULL,
            severity TEXT NOT NULL DEFAULT 'medium',
            status TEXT NOT NULL DEFAULT 'open',
            repair_cost REAL DEFAULT 0,
            resolved_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
        );
    ''')
    conn.commit()
    return conn


# ─── Helper ───────────────────────────────────────────────────────────────────

def make_vehicle_data(user_id=1, plate='34ABC123'):
    return {
        'user_id':    user_id,
        'brand':      'Toyota',
        'model':      'Corolla',
        'year':       2020,
        'plate':      plate,
        'current_km': 50000,
        'fuel_type':  'benzin',
        'motor':      '1.6',
        'color':      'Beyaz',
        'notes':      '',
    }


# ─── Validation Tests ─────────────────────────────────────────────────────────

class TestValidationFunctions(unittest.TestCase):

    def test_valid_email(self):
        self.assertTrue(is_valid_email('test@example.com'))
        self.assertTrue(is_valid_email('user.name+tag@domain.org'))

    def test_invalid_email(self):
        self.assertFalse(is_valid_email('notanemail'))
        self.assertFalse(is_valid_email('missing@'))
        self.assertFalse(is_valid_email('@nodomain.com'))
        self.assertFalse(is_valid_email(''))

    def test_valid_plate(self):
        self.assertTrue(is_valid_plate('34ABC123'))
        self.assertTrue(is_valid_plate('06 AB 1234'))
        self.assertTrue(is_valid_plate('61 A 1234'))

    def test_invalid_plate(self):
        self.assertFalse(is_valid_plate('ABCDEF'))
        self.assertFalse(is_valid_plate('123456'))
        self.assertFalse(is_valid_plate(''))

    def test_valid_year(self):
        self.assertTrue(is_valid_year(2020))
        self.assertTrue(is_valid_year('2015'))
        self.assertTrue(is_valid_year(1990))

    def test_invalid_year(self):
        self.assertFalse(is_valid_year(1800))
        self.assertFalse(is_valid_year('abc'))
        self.assertFalse(is_valid_year(None))
        self.assertFalse(is_valid_year(9999))

    def test_positive_number(self):
        self.assertTrue(is_positive_number(0))
        self.assertTrue(is_positive_number(100))
        self.assertTrue(is_positive_number('50000'))
        self.assertTrue(is_positive_number(3.14))

    def test_invalid_number(self):
        self.assertFalse(is_positive_number('abc'))
        self.assertFalse(is_positive_number(None))
        self.assertFalse(is_positive_number(''))

    def test_hash_password(self):
        h1 = hash_password('password123')
        h2 = hash_password('password123')
        h3 = hash_password('different')
        self.assertEqual(h1, h2)
        self.assertNotEqual(h1, h3)
        self.assertEqual(len(h1), 64)  # SHA-256 hex


# ─── Auth Tests ───────────────────────────────────────────────────────────────

class TestAuth(unittest.TestCase):

    def setUp(self):
        self.db = create_test_db()

    def tearDown(self):
        self.db.close()

    def test_register_success(self):
        result = register_user(self.db, 'testuser', 'test@example.com', 'password123')
        self.assertTrue(result['success'])

    def test_register_short_username(self):
        result = register_user(self.db, 'ab', 'test@example.com', 'password123')
        self.assertFalse(result['success'])
        self.assertIn('3 karakter', result['error'])

    def test_register_invalid_email(self):
        result = register_user(self.db, 'testuser', 'bademail', 'password123')
        self.assertFalse(result['success'])

    def test_register_short_password(self):
        result = register_user(self.db, 'testuser', 'test@example.com', '123')
        self.assertFalse(result['success'])
        self.assertIn('6 karakter', result['error'])

    def test_register_duplicate_email(self):
        register_user(self.db, 'user1', 'same@example.com', 'password123')
        result = register_user(self.db, 'user2', 'same@example.com', 'password123')
        self.assertFalse(result['success'])
        self.assertIn('kayıtlı', result['error'])

    def test_register_duplicate_username(self):
        register_user(self.db, 'sameuser', 'email1@example.com', 'password123')
        result = register_user(self.db, 'sameuser', 'email2@example.com', 'password123')
        self.assertFalse(result['success'])

    def test_login_success(self):
        register_user(self.db, 'testuser', 'test@example.com', 'password123')
        result = login_user(self.db, 'test@example.com', 'password123')
        self.assertTrue(result['success'])
        self.assertEqual(result['user']['username'], 'testuser')

    def test_login_wrong_password(self):
        register_user(self.db, 'testuser', 'test@example.com', 'password123')
        result = login_user(self.db, 'test@example.com', 'wrongpass')
        self.assertFalse(result['success'])

    def test_login_nonexistent_user(self):
        result = login_user(self.db, 'nobody@example.com', 'password123')
        self.assertFalse(result['success'])


# ─── Vehicle Tests ────────────────────────────────────────────────────────────

class TestVehicle(unittest.TestCase):

    def setUp(self):
        self.db = create_test_db()
        self.db.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
            ('testuser', 'test@example.com', hash_password('password123'))
        )
        self.db.commit()
        self.user_id = self.db.execute('SELECT id FROM users').fetchone()['id']

    def tearDown(self):
        self.db.close()

    def test_add_vehicle_success(self):
        result = add_vehicle(self.db, make_vehicle_data(self.user_id))
        self.assertTrue(result['success'])

    def test_add_vehicle_missing_brand(self):
        data = make_vehicle_data(self.user_id)
        data['brand'] = ''
        result = add_vehicle(self.db, data)
        self.assertFalse(result['success'])

    def test_add_vehicle_invalid_year(self):
        data = make_vehicle_data(self.user_id)
        data['year'] = 1800
        result = add_vehicle(self.db, data)
        self.assertFalse(result['success'])

    def test_add_vehicle_duplicate_plate(self):
        add_vehicle(self.db, make_vehicle_data(self.user_id, plate='34ABC123'))
        result = add_vehicle(self.db, make_vehicle_data(self.user_id, plate='34ABC123'))
        self.assertFalse(result['success'])
        self.assertIn('kayıtlı', result['error'])

    def test_add_vehicle_no_fuel_type_uses_default(self):
        data = make_vehicle_data(self.user_id)
        data['fuel_type'] = None
        result = add_vehicle(self.db, data)
        self.assertTrue(result['success'])
        row = self.db.execute('SELECT fuel_type FROM vehicles').fetchone()
        self.assertEqual(row['fuel_type'], 'benzin')

    def test_delete_vehicle(self):
        add_vehicle(self.db, make_vehicle_data(self.user_id))
        vehicle_id = self.db.execute('SELECT id FROM vehicles').fetchone()['id']
        from services import delete_vehicle
        result = delete_vehicle(self.db, vehicle_id, self.user_id)
        self.assertTrue(result['success'])
        row = self.db.execute('SELECT id FROM vehicles WHERE id=?', (vehicle_id,)).fetchone()
        self.assertIsNone(row)

    def test_update_vehicle_km(self):
        add_vehicle(self.db, make_vehicle_data(self.user_id))
        vehicle_id = self.db.execute('SELECT id FROM vehicles').fetchone()['id']
        result = update_vehicle_km(self.db, vehicle_id, self.user_id, 75000)
        self.assertTrue(result['success'])
        row = self.db.execute('SELECT current_km FROM vehicles WHERE id=?', (vehicle_id,)).fetchone()
        self.assertEqual(row['current_km'], 75000)

    def test_update_vehicle_km_invalid(self):
        add_vehicle(self.db, make_vehicle_data(self.user_id))
        vehicle_id = self.db.execute('SELECT id FROM vehicles').fetchone()['id']
        result = update_vehicle_km(self.db, vehicle_id, self.user_id, 'abc')
        self.assertFalse(result['success'])


# ─── Maintenance Tests ────────────────────────────────────────────────────────

class TestMaintenance(unittest.TestCase):

    def setUp(self):
        self.db = create_test_db()
        self.db.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
            ('testuser', 'test@example.com', hash_password('pass123'))
        )
        self.db.commit()
        self.user_id = self.db.execute('SELECT id FROM users').fetchone()['id']
        add_vehicle(self.db, make_vehicle_data(self.user_id))
        self.vehicle_id = self.db.execute('SELECT id FROM vehicles').fetchone()['id']

    def tearDown(self):
        self.db.close()

    def _make_maintenance(self):
        return {
            'vehicle_id':        self.vehicle_id,
            'maintenance_type':  'Yağ Değişimi',
            'date':              '2024-01-15',
            'km_at_service':     50000,
            'next_service_km':   60000,
            'next_service_date': '2025-01-15',
            'cost':              500,
            'service_provider':  'Test Servis',
            'notes':             '',
        }

    def test_add_maintenance_success(self):
        result = add_maintenance(self.db, self._make_maintenance())
        self.assertTrue(result['success'])

    def test_add_maintenance_missing_type(self):
        data = self._make_maintenance()
        data['maintenance_type'] = ''
        result = add_maintenance(self.db, data)
        self.assertFalse(result['success'])

    def test_add_maintenance_invalid_km(self):
        data = self._make_maintenance()
        data['km_at_service'] = 'abc'
        result = add_maintenance(self.db, data)
        self.assertFalse(result['success'])

    def test_add_maintenance_missing_date(self):
        data = self._make_maintenance()
        data['date'] = ''
        result = add_maintenance(self.db, data)
        self.assertFalse(result['success'])


# ─── Fault Tests ──────────────────────────────────────────────────────────────

class TestFault(unittest.TestCase):

    def setUp(self):
        self.db = create_test_db()
        self.db.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
            ('testuser', 'test@example.com', hash_password('pass123'))
        )
        self.db.commit()
        self.user_id = self.db.execute('SELECT id FROM users').fetchone()['id']
        add_vehicle(self.db, make_vehicle_data(self.user_id))
        self.vehicle_id = self.db.execute('SELECT id FROM vehicles').fetchone()['id']

    def tearDown(self):
        self.db.close()

    def _make_fault(self):
        return {
            'vehicle_id':    self.vehicle_id,
            'title':         'Motor Arızası',
            'description':   'Motor çalışmıyor',
            'category':      'motor',
            'km_at_fault':   50000,
            'date_reported': '2024-03-01',
            'severity':      'high',
            'status':        'open',
            'repair_cost':   2000,
            'resolved_date': None,
        }

    def test_add_fault_success(self):
        result = add_fault(self.db, self._make_fault())
        self.assertTrue(result['success'])

    def test_add_fault_missing_title(self):
        data = self._make_fault()
        data['title'] = ''
        result = add_fault(self.db, data)
        self.assertFalse(result['success'])

    def test_add_fault_missing_date(self):
        data = self._make_fault()
        data['date_reported'] = ''
        result = add_fault(self.db, data)
        self.assertFalse(result['success'])


# ─── Cost Calculation Tests ───────────────────────────────────────────────────

class TestCostCalculation(unittest.TestCase):

    def setUp(self):
        self.db = create_test_db()
        self.db.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
            ('testuser', 'test@example.com', hash_password('pass123'))
        )
        self.db.commit()
        self.user_id = self.db.execute('SELECT id FROM users').fetchone()['id']
        add_vehicle(self.db, make_vehicle_data(self.user_id))
        self.vehicle_id = self.db.execute('SELECT id FROM vehicles').fetchone()['id']

    def tearDown(self):
        self.db.close()

    def test_total_cost_empty(self):
        total = get_total_cost_by_vehicle(self.db, self.vehicle_id)
        self.assertEqual(total, 0)

    def test_total_cost_with_maintenance(self):
        add_maintenance(self.db, {
            'vehicle_id': self.vehicle_id,
            'maintenance_type': 'Yağ Değişimi',
            'date': '2024-01-01',
            'km_at_service': 50000,
            'next_service_km': None,
            'next_service_date': None,
            'cost': 500,
            'service_provider': '',
            'notes': '',
        })
        total = get_total_cost_by_vehicle(self.db, self.vehicle_id)
        self.assertEqual(total, 500)

    def test_total_cost_with_fault(self):
        add_fault(self.db, {
            'vehicle_id': self.vehicle_id,
            'title': 'Fren Arızası',
            'description': '',
            'category': 'fren',
            'km_at_fault': None,
            'date_reported': '2024-02-01',
            'severity': 'high',
            'status': 'open',
            'repair_cost': 1500,
            'resolved_date': None,
        })
        total = get_total_cost_by_vehicle(self.db, self.vehicle_id)
        self.assertEqual(total, 1500)

    def test_total_cost_combined(self):
        add_maintenance(self.db, {
            'vehicle_id': self.vehicle_id,
            'maintenance_type': 'Yağ Değişimi',
            'date': '2024-01-01',
            'km_at_service': 50000,
            'next_service_km': None,
            'next_service_date': None,
            'cost': 500,
            'service_provider': '',
            'notes': '',
        })
        add_fault(self.db, {
            'vehicle_id': self.vehicle_id,
            'title': 'Fren Arızası',
            'description': '',
            'category': 'fren',
            'km_at_fault': None,
            'date_reported': '2024-02-01',
            'severity': 'high',
            'status': 'open',
            'repair_cost': 1500,
            'resolved_date': None,
        })
        total = get_total_cost_by_vehicle(self.db, self.vehicle_id)
        self.assertEqual(total, 2000)


if __name__ == '__main__':
    unittest.main(verbosity=2)