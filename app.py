import sqlite3
from functools import wraps
from flask import Flask, g, session, flash, redirect, url_for, render_template, request
from services import register_user, login_user

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

if __name__ == '__main__':
    app.run(debug=True)