"""
Flask Web Application for Family Christmas Wish List

This application allows family members to:
- Add wishes to a shared list
- Reserve wishes (so others know it's being handled)
- Delete wishes
- View all wishes in a simple table
"""

from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

# Database configuration
DATABASE = 'wishlist.db'


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
    Creates the wishes table with required columns.
    """
    conn = get_db_connection()
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


@app.route('/')
def index():
    """
    Homepage route - displays all wishes in a table.
    Unreserved wishes are shown first (sorted by reserved status).
    """
    conn = get_db_connection()
    # Sort by reserved (0 first, then 1) so unreserved wishes appear at top
    wishes = conn.execute(
        'SELECT * FROM wishes ORDER BY reserved ASC, id DESC'
    ).fetchall()
    conn.close()
    
    # Count total wishes
    total_wishes = len(wishes)
    
    return render_template('index.html', wishes=wishes, total_wishes=total_wishes)


@app.route('/add', methods=['POST'])
def add_wish():
    """
    Add a new wish to the database.
    Accepts POST data with person_name, wish_text, and optional product_link.
    Redirects back to homepage after successful insertion.
    """
    person_name = request.form.get('person_name')
    wish_text = request.form.get('wish_text')
    product_link = request.form.get('product_link', '')
    
    # Validate required fields
    if person_name and wish_text:
        conn = get_db_connection()
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


if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    
    # Run the Flask app on localhost
    print("Starting Flask app on http://127.0.0.1:5000")
    print("Press CTRL+C to quit")
    app.run(debug=True, host='0.0.0.0', port=5000)
