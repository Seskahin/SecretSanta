"""
Flask Web Application for Family Christmas Wish List

This application allows family members to:
- Add wishes to a shared list
- Reserve wishes (so others know it's being handled)
- Delete wishes
- View all wishes in a simple table
- Admin can manage family members pool
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import sqlite3
import os

app = Flask(__name__)
# NOTE: In production, use a secure random key from environment variable:
# app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
app.secret_key = 'your-secret-key-change-this-in-production'

# Database configuration
DATABASE = 'wishlist.db'

# Admin credentials (in production, use environment variables and hashed passwords)
# NOTE: For production use:
# - Store credentials in environment variables
# - Use password hashing (bcrypt, werkzeug.security, etc.)
# - Use a strong password
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'


def get_db_connection():
    """
    Create and return a connection to the SQLite database.
    Sets row_factory to sqlite3.Row to access columns by name.
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Initialize the database if it doesn't exist.
    Creates the wishes and family_members tables with required columns.
    """
    conn = get_db_connection()
    
    # Create family_members table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS family_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    
    # Create wishes table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS wishes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_name TEXT NOT NULL,
            wish_text TEXT NOT NULL,
            product_link TEXT,
            reserved INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()


def login_required(f):
    """
    Decorator to require admin login for protected routes.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    """
    Homepage route - displays all wishes grouped by person in a table.
    Shows wishes for each family member.
    """
    conn = get_db_connection()
    
    # Get all family members
    family_members = conn.execute(
        'SELECT name FROM family_members ORDER BY name ASC'
    ).fetchall()
    
    # Get all wishes grouped by person
    wishes_by_person = {}
    for member in family_members:
        person_name = member['name']
        wishes = conn.execute(
            'SELECT * FROM wishes WHERE person_name = ? ORDER BY reserved ASC, id DESC',
            (person_name,)
        ).fetchall()
        wishes_by_person[person_name] = wishes
    
    conn.close()
    
    return render_template('index.html', wishes_by_person=wishes_by_person)


@app.route('/add', methods=['POST'])
def add_wish():
    """
    Add a new wish to the database.
    Accepts POST data with person_name, wish_text, and optional product_link.
    Only allows wishes for family members in the pool.
    Redirects back to homepage after successful insertion.
    """
    person_name = request.form.get('person_name')
    wish_text = request.form.get('wish_text')
    product_link = request.form.get('product_link', '')
    
    # Validate required fields
    if person_name and wish_text:
        conn = get_db_connection()
        
        # Check if person is in family members pool
        member = conn.execute(
            'SELECT id FROM family_members WHERE name = ?',
            (person_name,)
        ).fetchone()
        
        if member:
            conn.execute(
                'INSERT INTO wishes (person_name, wish_text, product_link) VALUES (?, ?, ?)',
                (person_name, wish_text, product_link)
            )
            conn.commit()
        
        conn.close()
    
    return redirect(url_for('index'))


@app.route('/reserve/<int:wish_id>', methods=['POST'])
def reserve_wish(wish_id):
    """
    Toggle the reserved status of a wish.
    If reserved (1), changes to unreserved (0), and vice versa.
    """
    conn = get_db_connection()
    
    # Get current reserved status
    wish = conn.execute('SELECT reserved FROM wishes WHERE id = ?', (wish_id,)).fetchone()
    
    if wish:
        # Toggle reserved status (0 -> 1 or 1 -> 0)
        new_status = 0 if wish['reserved'] == 1 else 1
        conn.execute('UPDATE wishes SET reserved = ? WHERE id = ?', (new_status, wish_id))
        conn.commit()
    
    conn.close()
    return redirect(url_for('index'))


@app.route('/delete/<int:wish_id>', methods=['POST'])
def delete_wish(wish_id):
    """
    Delete a wish from the database by its ID.
    """
    conn = get_db_connection()
    conn.execute('DELETE FROM wishes WHERE id = ?', (wish_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """
    Admin login page with basic authentication.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            return render_template('admin_login.html', error='Invalid credentials')
    
    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    """
    Logout admin user.
    """
    session.pop('logged_in', None)
    return redirect(url_for('index'))


@app.route('/admin')
@login_required
def admin_panel():
    """
    Admin panel to manage family members pool.
    """
    conn = get_db_connection()
    family_members = conn.execute(
        'SELECT * FROM family_members ORDER BY name ASC'
    ).fetchall()
    conn.close()
    
    return render_template('admin_panel.html', family_members=family_members)


@app.route('/admin/add_member', methods=['POST'])
@login_required
def add_family_member():
    """
    Add a new family member to the pool.
    """
    name = request.form.get('name')
    
    if name:
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO family_members (name) VALUES (?)',
                (name,)
            )
            conn.commit()
            flash(f'Successfully added {name} to the family pool!', 'success')
        except sqlite3.IntegrityError:
            # Name already exists
            flash(f'Error: {name} already exists in the family pool.', 'error')
        conn.close()
    
    return redirect(url_for('admin_panel'))


@app.route('/admin/delete_member/<int:member_id>', methods=['POST'])
@login_required
def delete_family_member(member_id):
    """
    Delete a family member from the pool.
    Also deletes all wishes associated with that member.
    """
    conn = get_db_connection()
    
    # Get the member name first
    member = conn.execute(
        'SELECT name FROM family_members WHERE id = ?',
        (member_id,)
    ).fetchone()
    
    if member:
        # Delete all wishes for this member
        conn.execute('DELETE FROM wishes WHERE person_name = ?', (member['name'],))
        
        # Delete the member
        conn.execute('DELETE FROM family_members WHERE id = ?', (member_id,))
        conn.commit()
    
    conn.close()
    return redirect(url_for('admin_panel'))


@app.route('/admin/edit_member/<int:member_id>', methods=['POST'])
@login_required
def edit_family_member(member_id):
    """
    Edit a family member's name.
    Also updates all wishes with the old name to use the new name.
    """
    new_name = request.form.get('name')
    
    if new_name:
        conn = get_db_connection()
        
        # Get the old name
        member = conn.execute(
            'SELECT name FROM family_members WHERE id = ?',
            (member_id,)
        ).fetchone()
        
        if member:
            old_name = member['name']
            
            try:
                # Update the member name
                conn.execute(
                    'UPDATE family_members SET name = ? WHERE id = ?',
                    (new_name, member_id)
                )
                
                # Update all wishes with the old name
                conn.execute(
                    'UPDATE wishes SET person_name = ? WHERE person_name = ?',
                    (new_name, old_name)
                )
                
                conn.commit()
                flash(f'Successfully updated {old_name} to {new_name}!', 'success')
            except sqlite3.IntegrityError:
                # Name already exists
                flash(f'Error: {new_name} already exists in the family pool.', 'error')
        
        conn.close()
    
    return redirect(url_for('admin_panel'))


if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    
    # Run the Flask app on localhost
    # Note: debug=True is enabled for local development only
    # For production, use a proper WSGI server like gunicorn
    print("Starting Flask app on http://127.0.0.1:5000")
    print("Press CTRL+C to quit")
    app.run(debug=True, host='0.0.0.0', port=5000)
