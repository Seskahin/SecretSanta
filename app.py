"""
Flask Web Application for Family Christmas Wish List

This application allows family members to:
- Add wishes to a shared list
- Delete wishes
- View all wishes in a simple table
- Admin can manage family members pool and run Secret Santa assignments
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from markupsafe import Markup, escape
import random
import sqlite3
import os
from datetime import date

app = Flask(__name__)
# NOTE: In production, use a secure random key from environment variable:
# app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
app.secret_key = 'your-secret-key-change-this-in-production'


@app.template_filter('nl2br')
def nl2br_filter(value):
    """Convert newlines in text to HTML <br> tags, safely escaping HTML."""
    return Markup(escape(value).replace('\n', Markup('<br>\n')))

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
    Creates the wishes, family_members, and secret_santa tables.
    """
    conn = get_db_connection()
    
    # Create family_members table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS family_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            team_name TEXT
        )
    ''')

    # Migration: add team_name column if it doesn't exist yet
    try:
        conn.execute('ALTER TABLE family_members ADD COLUMN team_name TEXT')
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists
    
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

    # Create secret_santa table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS secret_santa (
            giver_name TEXT PRIMARY KEY,
            receiver_name TEXT NOT NULL
        )
    ''')

    # Create settings table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    conn.commit()
    conn.close()


def get_setting(key, default=None):
    """Return the value for a settings key, or default if not set."""
    conn = get_db_connection()
    row = conn.execute('SELECT value FROM settings WHERE key = ?', (key,)).fetchone()
    conn.close()
    return row['value'] if row else default


def set_setting(key, value):
    """Insert or replace a setting key/value pair."""
    conn = get_db_connection()
    conn.execute(
        'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
        (key, value)
    )
    conn.commit()
    conn.close()


def wishes_locked():
    """Return True if today is strictly after the configured deadline.
    The deadline date itself is the last day wishes can be added (inclusive)."""
    deadline_str = get_setting('wish_deadline')
    if not deadline_str:
        return False
    try:
        deadline = date.fromisoformat(deadline_str)
        return date.today() > deadline
    except ValueError:
        return False


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
    Homepage route - redirects to who_are_you if no identity selected,
    otherwise redirects to my_wishlist.
    """
    if session.get('selected_members'):
        return redirect(url_for('my_wishlist'))
    return redirect(url_for('who_are_you'))


@app.route('/add', methods=['POST'])
def add_wish():
    """
    Add a new wish to the database.
    Accepts POST data with person_name, wish_text, and optional product_link.
    Only allows wishes for family members in the pool.
    Blocked after the configured wish deadline.
    If the wish is for someone other than the current user, a flash message is
    shown instead of displaying the wish.
    Redirects back to the source page after successful insertion.
    """
    person_name = request.form.get('person_name')
    wish_text = request.form.get('wish_text')
    product_link = request.form.get('product_link', '')
    source = request.form.get('source', '')

    # Block new wishes after the deadline
    if wishes_locked():
        flash('Wishes are no longer accepted — the deadline has passed.', 'error')
        if source == 'my_wishlist':
            return redirect(url_for('my_wishlist'))
        return redirect(url_for('index'))

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

            # If wishing on behalf of another member, show confirmation only
            selected_members = session.get('selected_members', [])
            if person_name not in selected_members:
                flash(f'🎁 Wish created for {person_name}!', 'success')

        conn.close()

    if source == 'my_wishlist':
        return redirect(url_for('my_wishlist'))
    return redirect(url_for('index'))


@app.route('/delete/<int:wish_id>', methods=['POST'])
def delete_wish(wish_id):
    """
    Delete a wish from the database by its ID.
    """
    source = request.form.get('source', '')
    conn = get_db_connection()
    conn.execute('DELETE FROM wishes WHERE id = ?', (wish_id,))
    conn.commit()
    conn.close()
    
    if source == 'my_wishlist':
        return redirect(url_for('my_wishlist'))
    return redirect(url_for('index'))


@app.route('/who_are_you', methods=['GET', 'POST'])
def who_are_you():
    """
    Page where user selects which family member(s) they are.
    Stores selection in session and redirects to personalized wishlist.
    """
    conn = get_db_connection()
    family_members = conn.execute(
        'SELECT name FROM family_members ORDER BY name ASC'
    ).fetchall()
    conn.close()

    if request.method == 'POST':
        selected = request.form.getlist('selected_members')
        if selected:
            session['selected_members'] = selected
            return redirect(url_for('my_wishlist'))
        return render_template('who_are_you.html', family_members=family_members,
                               error='Please select a family member.')

    return render_template('who_are_you.html', family_members=family_members)


@app.route('/my_wishlist')
def my_wishlist():
    """
    Personalized wishlist view: shows own wishes and the wishes of the
    Secret Santa receiver for each selected family member.
    """
    selected_members = session.get('selected_members', [])
    if not selected_members:
        return redirect(url_for('who_are_you'))

    conn = get_db_connection()

    # Validate selected members still exist
    placeholders = ','.join(['?'] * len(selected_members))
    query = 'SELECT name FROM family_members WHERE name IN (' + placeholders + ')'
    valid = conn.execute(query, selected_members).fetchall()
    valid_names = [r['name'] for r in valid]
    if not valid_names:
        session.pop('selected_members', None)
        conn.close()
        return redirect(url_for('who_are_you'))

    # Get Secret Santa assignments for selected members
    assigned_to = {}
    for name in valid_names:
        assignment = conn.execute(
            'SELECT receiver_name FROM secret_santa WHERE giver_name = ?',
            (name,)
        ).fetchone()
        if assignment:
            assigned_to[name] = assignment['receiver_name']

    # Build set of all relevant names: own + assigned receivers
    names_to_show = set(valid_names)
    for receiver in assigned_to.values():
        names_to_show.add(receiver)

    # Get all family members for the add-wish dropdown (own + all for impersonation)
    all_family_members = conn.execute(
        'SELECT name FROM family_members ORDER BY name ASC'
    ).fetchall()

    # Get wishes for all relevant people
    wishes_by_person = {}
    for person_name in names_to_show:
        wishes = conn.execute(
            'SELECT * FROM wishes WHERE person_name = ? ORDER BY id DESC',
            (person_name,)
        ).fetchall()
        wishes_by_person[person_name] = wishes

    conn.close()

    locked = wishes_locked()
    wish_deadline = get_setting('wish_deadline')

    return render_template('my_wishlist.html',
                           wishes_by_person=wishes_by_person,
                           selected_members=valid_names,
                           assigned_to=assigned_to,
                           all_family_members=all_family_members,
                           wishes_locked=locked,
                           wish_deadline=wish_deadline)



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
    return redirect(url_for('who_are_you'))


@app.route('/admin')
@login_required
def admin_panel():
    """
    Admin panel to manage family members pool, Secret Santa, and view all wishes.
    """
    conn = get_db_connection()
    family_members = conn.execute(
        'SELECT * FROM family_members ORDER BY name ASC'
    ).fetchall()
    secret_santa = conn.execute(
        'SELECT * FROM secret_santa ORDER BY giver_name ASC'
    ).fetchall()
    all_wishes = conn.execute(
        'SELECT * FROM wishes ORDER BY person_name ASC, id DESC'
    ).fetchall()
    conn.close()

    wish_deadline = get_setting('wish_deadline')

    return render_template('admin_panel.html', family_members=family_members,
                           secret_santa=secret_santa, all_wishes=all_wishes,
                           wish_deadline=wish_deadline)


@app.route('/admin/set_deadline', methods=['POST'])
@login_required
def set_deadline():
    """
    Save or clear the wish deadline date.
    """
    deadline = request.form.get('wish_deadline', '').strip()
    if deadline:
        set_setting('wish_deadline', deadline)
        flash(f'Wish deadline set to {deadline}.', 'success')
    else:
        set_setting('wish_deadline', '')
        flash('Wish deadline cleared — wishes can be added at any time.', 'success')
    return redirect(url_for('admin_panel'))


@app.route('/admin/run_secret_santa', methods=['POST'])
@login_required
def run_secret_santa():
    """
    Run the Secret Santa assignment: creates a random circular assignment
    where each person gives to exactly one other person and no one is
    assigned to a member of their own team.
    """
    conn = get_db_connection()
    members = conn.execute(
        'SELECT name, team_name FROM family_members ORDER BY name ASC'
    ).fetchall()
    names = [m['name'] for m in members]
    teams = {m['name']: m['team_name'] for m in members}

    if len(names) < 2:
        flash('Need at least 2 family members for Secret Santa!', 'error')
        conn.close()
        return redirect(url_for('admin_panel'))

    # Try to find a valid circular assignment that respects team constraints.
    # Two members violate the constraint if both have the same non-None team.
    assignment = None
    MAX_ATTEMPTS = 200
    for _ in range(MAX_ATTEMPTS):
        shuffled = names[:]
        random.shuffle(shuffled)
        valid = True
        for i, giver in enumerate(shuffled):
            receiver = shuffled[(i + 1) % len(shuffled)]
            giver_team = teams.get(giver)
            receiver_team = teams.get(receiver)
            if giver_team and giver_team == receiver_team:
                valid = False
                break
        if valid:
            assignment = shuffled
            break

    if assignment is None:
        flash(
            'Could not create a valid Secret Santa assignment with the current team '
            'constraints. Try adding more participants or adjusting team sizes.',
            'error'
        )
        conn.close()
        return redirect(url_for('admin_panel'))

    conn.execute('DELETE FROM secret_santa')
    for i, giver in enumerate(assignment):
        receiver = assignment[(i + 1) % len(assignment)]
        conn.execute(
            'INSERT INTO secret_santa (giver_name, receiver_name) VALUES (?, ?)',
            (giver, receiver)
        )
    conn.commit()
    conn.close()
    flash('Secret Santa assignments created successfully!', 'success')
    return redirect(url_for('admin_panel'))


@app.route('/admin/add_member', methods=['POST'])
@login_required
def add_family_member():
    """
    Add a new family member to the pool.
    """
    name = request.form.get('name')
    team_name = request.form.get('team_name', '').strip() or None
    
    if name:
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO family_members (name, team_name) VALUES (?, ?)',
                (name, team_name)
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
    Edit a family member's name and team.
    Also updates all wishes with the old name to use the new name.
    """
    new_name = request.form.get('name')
    team_name = request.form.get('team_name', '').strip() or None
    
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
                # Update the member name and team
                conn.execute(
                    'UPDATE family_members SET name = ?, team_name = ? WHERE id = ?',
                    (new_name, team_name, member_id)
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
