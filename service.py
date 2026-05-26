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