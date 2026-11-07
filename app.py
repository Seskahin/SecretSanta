"""
Flask Web Application for Family Christmas Wish List

This application allows family members to:
- Add wishes to a shared list
- Delete wishes
- View all wishes in a simple table
- Admin can manage family members pool and run Secret Santa assignments
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response, jsonify
from functools import wraps
from markupsafe import Markup, escape
import random
import json
import sqlite3
import os
import time
from datetime import date, datetime, timedelta, timezone
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

load_dotenv()

app = Flask(__name__)
# WARNING: Without SECRET_KEY set, a new random key is generated on every restart,
# invalidating all user sessions. Set SECRET_KEY in your environment or .env file.
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

app.config.update(
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(days=3650),
)

LOCAL_TIMEZONE = ZoneInfo('Europe/Berlin')

SUPPORTED_LANGUAGES = {'de': 'Deutsch'}

TRANSLATIONS = {
    'en': {
        'title': 'Family Christmas Wish List',
        'header': '🎄 Family Christmas Wish List 🎅',
        'admin': '⚙️ Admin',
        'logout': 'Logout',
        'back_to_wishlist': '← Back to My Wishlist',
        'change_language': '🌐 Language',
        'language_popup_title': 'Choose Your Language',
        'language_popup_desc': 'Please select your preferred language:',
        'confirm_language': 'Confirm',
        'who_are_you': 'Who Are You?',
        'select_name': 'Select your name(s) to see your personal wishlist.',
        'select_members': '🎁 Select your family member name(s):',
        'team_restriction_hint': 'Tip: Once you select a member from a team, only other members of the same team can be added.',
        'different_team_error': 'You can only select members from the same team.',
        'view_wishlist': '🎅 View My Wishlist',
        'no_members': 'No family members in the pool yet. Please ask the admin to add family members first! 👨‍👩‍👧‍👦',
        'please_select': 'Please select at least one family member.',
        'my_wishlist': '🎁 My Wishlist',
        'viewing_as': 'Viewing as:',
        'secret_santa': 'Secret Santa:',
        'buys_for': '→ buys for',
        'no_assignments': 'No Secret Santa assignments yet. Ask the admin to run Secret Santa!',
        'wishes_closed': 'The wish list is now closed.',
        'deadline_was': 'The deadline was',
        'no_new_wishes': 'No new wishes can be added — the list is read-only.',
        'add_wish': 'Add a Wish',
        'add_wish_desc': 'You can add a wish for yourself or on behalf of another family member. Wishes added for other members will not be visible to you (except your Secret Santa receiver\'s wishes shown below).',
        'for_label': 'For:',
        'select_name_opt': 'Select a name',
        'you_suffix': '(you)',
        'wish_required': 'Wish (required):',
        'product_link_label': 'Product Link (optional):',
        'add_wish_btn': 'Add Wish',
        'your_wishes': 'Your Wishes',
        'wishes_label': '\'s Wishes',
        'no_wishes_for': 'No wishes added yet for',
        'buying_for': 'You Are Buying For',
        'buying_for_icon': '🛍️',
        'delete': 'Delete',
        'delete_wish_confirm': 'Are you sure you want to delete this wish?',
        'progress_label': 'users have already chosen a wish',
        'days_left': 'days left until deadline',
        'deadline_passed': 'Deadline has passed',
        'no_deadline': 'No deadline set',
        'comments': '💬 Comments',
        'add_comment': 'Add a Comment',
        'comment_text': 'Comment:',
        'your_name_label': 'Your name (optional, leave blank for anonymous):',
        'post_comment': 'Post Comment',
        'anonymous': 'Anonymous',
        'no_comments': 'No comments yet. Be the first to comment!',
        'admin_title': 'Admin - Manage Family Members',
        'wish_deadline_section': '📅 Wish Deadline',
        'deadline_desc': 'After this date, the wish list becomes read-only and no new wishes can be added. Leave blank to allow wishes at any time.',
        'deadline_inclusive': 'Deadline date (inclusive):',
        'save_deadline': 'Save Deadline',
        'current_deadline': 'Current deadline:',
        'no_deadline_set': 'No deadline set — wishes can be added at any time.',
        'add_member': 'Add Family Member',
        'member_name': 'Family Member Name:',
        'team_optional': 'Team (optional, e.g. "Team A"):',
        'no_team': 'Leave blank if no team',
        'add_member_btn': 'Add Member',
        'family_pool': 'Family Members Pool',
        'no_members_yet': 'No family members yet. Add the first one above! 👨‍👩‍👧‍👦',
        'name_col': 'Name',
        'team_col': 'Team',
        'actions_col': 'Actions',
        'update_btn': 'Update',
        'secret_santa_admin': '🎅 Secret Santa Assignments',
        'run_ss': 'Run Secret Santa',
        'run_ss_confirm': 'This will overwrite existing Secret Santa assignments. Continue?',
        'giver': 'Giver',
        'receiver': '→ Buys for',
        'no_ss': 'No Secret Santa assignments yet. Click "Run Secret Santa" to generate them.',
        'all_wishes': '📋 All Wishes',
        'person_col': 'Person',
        'wish_col': 'Wish',
        'product_col': 'Product Link',
        'view_product': 'View Product',
        'no_wishes_admin': 'No wishes added yet.',
        'reset_section': '🔄 Reset',
        'reset_btn': 'Reset All Wishes, Assignments & Comments',
        'reset_confirm': 'This will delete ALL wishes, ALL Secret Santa assignments, and ALL comments. Are you sure?',
        'reset_desc': 'This will delete all wishes, reset the Secret Santa assignments, and delete all comments.',
        'delete_member_confirm': 'Are you sure? This will also delete all wishes for',
    },
    'de': {
        'title': 'Familien Weihnachts-Wunschliste',
        'header': '🎄 Familien Weihnachts-Wunschliste 🎅',
        'admin': '⚙️ Admin',
        'logout': 'Abmelden',
        'back_to_wishlist': '← Zurück zur Wunschliste',
        'change_language': '🌐 Sprache',
        'language_popup_title': 'Sprache wählen',
        'language_popup_desc': 'Bitte wähle deine bevorzugte Sprache:',
        'confirm_language': 'Bestätigen',
        'who_are_you': 'Wer bist du?',
        'select_name': 'Wähle deinen Namen, um deine persönliche Wunschliste zu sehen.',
        'select_members': '🎁 Wähle deinen Familiennamen:',
        'team_restriction_hint': 'Tipp: Sobald du ein Mitglied eines Teams auswählst, können nur weitere Mitglieder desselben Teams hinzugefügt werden.',
        'different_team_error': 'Du kannst nur Mitglieder desselben Teams auswählen.',
        'view_wishlist': '🎅 Meine Wunschliste anzeigen',
        'no_members': 'Noch keine Familienmitglieder. Bitte den Admin, Familienmitglieder hinzuzufügen! 👨‍👩‍👧‍👦',
        'please_select': 'Bitte wähle mindestens ein Familienmitglied aus.',
        'my_wishlist': '🎁 Meine Wunschliste',
        'viewing_as': 'Angemeldet als:',
        'secret_santa': 'Wichteln:',
        'buys_for': '→ kauft für',
        'no_assignments': 'Noch keine Wichtel-Zuteilung. Bitte den Admin, das Wichteln zu starten!',
        'wishes_closed': 'Die Wunschliste ist jetzt geschlossen.',
        'deadline_was': 'Der Einsendeschluss war',
        'no_new_wishes': 'Es können keine neuen Wünsche hinzugefügt werden — die Liste ist schreibgeschützt.',
        'add_wish': 'Wunsch hinzufügen',
        'add_wish_desc': 'Du kannst einen Wunsch für dich oder stellvertretend für ein anderes Familienmitglied hinzufügen.',
        'for_label': 'Für:',
        'select_name_opt': 'Name auswählen',
        'you_suffix': '(du)',
        'wish_required': 'Wunsch (erforderlich):',
        'product_link_label': 'Produktlink (optional):',
        'add_wish_btn': 'Wunsch hinzufügen',
        'your_wishes': 'Deine Wünsche',
        'wishes_label': 's Wünsche',
        'no_wishes_for': 'Noch keine Wünsche für',
        'buying_for': 'Du kaufst für',
        'buying_for_icon': '🛍️',
        'delete': 'Löschen',
        'delete_wish_confirm': 'Möchtest du diesen Wunsch wirklich löschen?',
        'progress_label': 'Nutzer haben bereits einen Wunsch eingetragen',
        'days_left': 'Tage bis zum Einsendeschluss',
        'deadline_passed': 'Einsendeschluss ist vorbei',
        'no_deadline': 'Kein Einsendeschluss gesetzt',
        'assignment_date_section': '🎁 Termin der Wichtel-Zuteilung',
        'assignment_date_desc': 'Dieses Datum dient nur als Hinweis. Die Zuteilung wird weiterhin manuell durch den Admin gestartet.',
        'assignment_date_label': 'Datum der Zuteilung:',
        'save_assignment_date': 'Termin speichern',
        'current_assignment_date': 'Aktueller Zuteilungstermin:',
        'no_assignment_date': 'Kein Zuteilungstermin festgelegt.',
        'assignment_days_left': 'Tage bis zur Wichtel-Zuteilung',
        'assignment_today': 'Die Wichtel-Zuteilung ist für heute vorgemerkt.',
        'assignment_date_passed': 'Der geplante Zuteilungstermin ist vorbei.',
        'identity_hint_title': 'Hinweis zur Auswahl',
        'identity_hint_text': 'Wähle dich einmal aus und markiere alle Personen in deinem Haushalt, für die du ebenfalls Geschenke besorgen möchtest.',
        'identity_hint_close': 'Verstanden',
        'gift_limit_reached': 'Für {person_name} wurden bereits maximal {limit} Wünsche eingetragen. Der weitere Wunsch wurde nicht hinzugefügt.',
        'gift_limit_hint': '{person_name} hat bereits {count} von {limit} möglichen Wünschen.',
        'preview_title': 'Wunschvorschau von einem artigen Kind',
        'preview_title_limit': 'Wunschvorschau von einem Kind',
        'assignment_notification': 'Die Wichtel-Zuteilung wurde durchgeführt. Du kannst jetzt nachsehen, für wen du ein Geschenk besorgst.',
        'preview_empty': 'Noch keine Vorschau verfügbar.',
        'gift_limit_section': '🎁 Wunschlimit',
        'gift_limit_desc': 'Maximale Anzahl von Wünschen pro Person.',
        'gift_limit_label': 'Maximale Wünsche:',
        'save_gift_limit': 'Limit speichern',
        'current_gift_limit': 'Aktuelles Limit:',
        'preview_interval_section': '🔄 Wunschvorschau',
        'preview_interval_desc': 'Die rechte Wunschvorschau zeigt zufällig eine teilnehmende Person.',
        'preview_interval_label': 'Wechselintervall in Sekunden:',
        'save_preview_interval': 'Intervall speichern',
        'current_preview_interval': 'Aktuelles Intervall:',
        'comments': '💬 Kommentare',
        'add_comment': 'Kommentar hinzufügen',
        'comment_text': 'Kommentar:',
        'your_name_label': 'Dein Name (optional, leer lassen für anonym):',
        'post_comment': 'Kommentar posten',
        'anonymous': 'Anonym',
        'no_comments': 'Noch keine Kommentare. Sei der Erste!',
        'admin_title': 'Admin - Familienmitglieder verwalten',
        'wish_deadline_section': '📅 Einsendeschluss',
        'deadline_desc': 'Nach diesem Datum wird die Wunschliste schreibgeschützt und es können keine neuen Wünsche hinzugefügt werden.',
        'deadline_inclusive': 'Einsendeschluss (inklusive):',
        'save_deadline': 'Einsendeschluss speichern',
        'current_deadline': 'Aktueller Einsendeschluss:',
        'no_deadline_set': 'Kein Einsendeschluss — Wünsche können jederzeit hinzugefügt werden.',
        'add_member': 'Familienmitglied hinzufügen',
        'member_name': 'Name des Familienmitglieds:',
        'team_optional': 'Team (optional, z.B. "Team A"):',
        'no_team': 'Leer lassen, wenn kein Team',
        'add_member_btn': 'Mitglied hinzufügen',
        'family_pool': 'Familienmitglieder Pool',
        'participation': 'Wichtelteilnahme',
        'participation_hint': 'Soll diese Person am Wichteln teilnehmen?',
        'save_participation': 'Teilnahme speichern',
        'no_members_yet': 'Noch keine Familienmitglieder. Füge das erste oben hinzu! 👨‍👩‍👧‍👦',
        'name_col': 'Name',
        'team_col': 'Team',
        'actions_col': 'Aktionen',
        'update_btn': 'Aktualisieren',
        'secret_santa_admin': '🎅 Wichtel-Zuteilung',
        'run_ss': 'Wichteln starten',
        'run_ss_confirm': 'Dies wird bestehende Wichtel-Zuteilungen überschreiben. Fortfahren?',
        'giver': 'Geber',
        'receiver': '→ Kauft für',
        'no_ss': 'Noch keine Wichtel-Zuteilung. Klicke auf "Wichteln starten".',
        'all_wishes': '📋 Alle Wünsche',
        'person_col': 'Person',
        'wish_col': 'Wunsch',
        'product_col': 'Produktlink',
        'view_product': 'Produkt ansehen',
        'no_wishes_admin': 'Noch keine Wünsche eingetragen.',
        'reset_section': '🔄 Zurücksetzen',
        'reset_btn': 'Zurücksetzen',
        'reset_confirm': 'Bist du sicher?',
        'reset_desc': 'Setze Wünsche, die Wichtel-Zuteilung und Kommentare unabhängig voneinander zurück.',
        'delete_member_confirm': 'Bist du sicher? Dadurch werden auch alle Wünsche für',
    },
}


@app.template_filter('nl2br')
def nl2br_filter(value):
    """Convert newlines in text to HTML <br> tags, safely escaping HTML."""
    return Markup(escape(value).replace('\n', Markup('<br>\n')))


def get_language():
    """Return the application's fixed language."""
    return 'de'


def format_comment_local_time(timestamp):
    """Convert a stored UTC comment timestamp to German local time."""
    try:
        utc_timestamp = datetime.strptime(
            timestamp, '%Y-%m-%d %H:%M'
        ).replace(tzinfo=timezone.utc)
        return utc_timestamp.astimezone(LOCAL_TIMEZONE).strftime('%d.%m.%Y %H:%M')
    except (TypeError, ValueError):
        return timestamp


GIFT_IMAGES = (
    'red_yellow_gift.png',
    'green_red_gift.png',
    'blue_yellow.png',
)


def get_gift_positions(wish_count):
    """Return persistent random decoration data, adding entries only as needed."""
    stored = get_setting('gift_positions', '[]')
    try:
        parsed_positions = json.loads(stored)
    except (TypeError, ValueError):
        parsed_positions = []
    if not isinstance(parsed_positions, list):
        parsed_positions = []

    positions = [position for position in parsed_positions if isinstance(position, dict)]
    changed = len(positions) != len(parsed_positions)
    if len(positions) > wish_count:
        positions = positions[:wish_count]
        changed = True

    while len(positions) < wish_count:
        side = random.choice(('left', 'right'))
        position = {
            'side': side,
            'offset': random.randint(2, 17),
            'top': random.randint(6, 92),
            'size': random.randint(35, 150),
            'rotation': random.randint(-35, 35),
            'image': random.choice(GIFT_IMAGES),
        }
        positions.append(position)
        changed = True

    if changed:
        set_setting('gift_positions', json.dumps(positions))
    return positions


@app.before_request
def make_session_permanent():
    """Keep the identity selection in a persistent browser cookie."""
    session.permanent = True


@app.context_processor
def inject_translations():
    """Inject translation dict and language info into every template."""
    lang = get_language()
    conn = get_db_connection()
    active_wish_count = conn.execute('SELECT COUNT(*) FROM wishes').fetchone()[0]
    conn.close()
    gift_positions = get_gift_positions(active_wish_count)
    global_popup = None
    announcement_version = get_setting('assignment_announcement_version')
    if announcement_version and session.get('assignment_announcement_version') != announcement_version:
        global_popup = get_setting(
            'assignment_announcement_message',
            TRANSLATIONS['de']['assignment_notification']
        )
        session['assignment_announcement_version'] = announcement_version
    return {
        't': TRANSLATIONS[lang],
        'lang': lang,
        'supported_languages': SUPPORTED_LANGUAGES,
        'preview_interval': get_preview_interval(),
        'active_wish_count': active_wish_count,
        'gift_positions': gift_positions,
        'wish_popup': session.pop('wish_popup', None),
        'global_popup': global_popup,
        'show_preview': request.endpoint in {'my_wishlist', 'admin_panel'},
    }


def get_gift_limit():
    """Return the configured maximum number of wishes per person."""
    try:
        return max(1, int(get_setting('gift_limit', '5')))
    except (TypeError, ValueError):
        return 5


def get_preview_interval():
    """Return the configured sidebar preview interval in seconds."""
    try:
        return max(5, int(get_setting('preview_interval', '30')))
    except (TypeError, ValueError):
        return 30


def get_preview_person(rotate=False):
    """Return the stored preview person, or choose a new one when rotating."""
    conn = get_db_connection()
    people = conn.execute(
        'SELECT fm.name FROM family_members fm '
        'JOIN wishes w ON w.person_name = fm.name '
        'WHERE fm.include_in_assignment = 1 '
        'GROUP BY fm.name HAVING COUNT(w.id) >= 2'
    ).fetchall()
    if not people:
        session.pop('preview_person_name', None)
        conn.close()
        return None
    available_names = {person['name'] for person in people}
    person_name = session.get('preview_person_name')
    if rotate or person_name not in available_names:
        rotation_candidates = [
            person['name'] for person in people
            if person['name'] != person_name
        ]
        person_name = random.choice(rotation_candidates or list(available_names))
        session['preview_person_name'] = person_name
    wishes = conn.execute(
        'SELECT wish_text, product_link FROM wishes '
        'WHERE person_name = ? ORDER BY id DESC',
        (person_name,)
    ).fetchall()
    conn.close()
    return {
        'person_name': person_name,
        'wishes': wishes,
        'at_limit': len(wishes) >= get_gift_limit(),
    }

# Database configuration
DATABASE = 'wishlist.db'

# Admin credentials — configure via environment variables for production use.
# Set ADMIN_USERNAME and ADMIN_PASSWORD as environment variables.
# Defaults below are for local development only.
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')


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
            team_name TEXT,
            include_in_assignment INTEGER NOT NULL DEFAULT 1
        )
    ''')

    # Migration: add team_name column if it doesn't exist yet
    try:
        conn.execute('ALTER TABLE family_members ADD COLUMN team_name TEXT')
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        conn.execute(
            'ALTER TABLE family_members ADD COLUMN include_in_assignment '
            'INTEGER NOT NULL DEFAULT 1'
        )
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

    # Create comments table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author_name TEXT,
            comment_text TEXT NOT NULL,
            created_at TEXT NOT NULL
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
        session['wish_popup'] = 'Es werden keine Wünsche mehr angenommen – der Einsendeschluss ist vorbei.'
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
            gift_limit = get_gift_limit()
            wish_count = conn.execute(
                'SELECT COUNT(*) FROM wishes WHERE person_name = ?',
                (person_name,)
            ).fetchone()[0]
            if wish_count >= gift_limit:
                session['wish_popup'] = TRANSLATIONS['de']['gift_limit_reached'].format(
                    person_name=person_name, limit=gift_limit
                )
            else:
                conn.execute(
                    'INSERT INTO wishes (person_name, wish_text, product_link) VALUES (?, ?, ?)',
                    (person_name, wish_text, product_link)
                )
                conn.commit()

            session['wish_popup'] = f'🎁 Wunsch für {person_name} wurde erstellt!'

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
    Only members from the same team may be selected together.
    """
    conn = get_db_connection()
    family_members = conn.execute(
        "SELECT name, COALESCE(team_name, '') AS team_name FROM family_members ORDER BY team_name, name ASC"
    ).fetchall()
    conn.close()

    if request.method == 'POST':
        selected = request.form.getlist('selected_members')
        if selected:
            # Validate that all selected members belong to the same team
            conn = get_db_connection()
            placeholders = ','.join(['?'] * len(selected))
            members_data = conn.execute(
                'SELECT team_name FROM family_members WHERE name IN (' + placeholders + ')',
                selected
            ).fetchall()
            conn.close()
            teams = set(m['team_name'] for m in members_data)
            if len(teams) > 1:
                return render_template('who_are_you.html', family_members=family_members,
                                       error=TRANSLATIONS[get_language()]['different_team_error'])
            session['selected_members'] = selected
            return redirect(url_for('my_wishlist'))
        return render_template('who_are_you.html', family_members=family_members,
                               error=TRANSLATIONS[get_language()]['please_select'])

    # If user already has a selection, go straight to the wishlist
    if session.get('selected_members'):
        return redirect(url_for('my_wishlist'))

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
        'SELECT fm.name, fm.include_in_assignment, COUNT(w.id) AS wish_count '
        'FROM family_members fm LEFT JOIN wishes w ON w.person_name = fm.name '
        'GROUP BY fm.id ORDER BY fm.name ASC'
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

    # Gather comments
    conn2 = get_db_connection()
    comment_rows = conn2.execute(
        'SELECT * FROM comments ORDER BY id DESC'
    ).fetchall()
    comments = []
    for comment in comment_rows:
        comment_data = dict(comment)
        comment_data['created_at'] = format_comment_local_time(comment['created_at'])
        comments.append(comment_data)
    # Progress: count distinct members with at least one wish vs total
    total_members = conn2.execute('SELECT COUNT(*) FROM family_members').fetchone()[0]
    members_with_wishes = conn2.execute(
        'SELECT COUNT(DISTINCT person_name) FROM wishes'
    ).fetchone()[0]
    conn2.close()

    return render_template('my_wishlist.html',
                           wishes_by_person=wishes_by_person,
                           selected_members=valid_names,
                           assigned_to=assigned_to,
                           all_family_members=all_family_members,
                           wishes_locked=locked,
                           wish_deadline=wish_deadline,
                           assignment_date=get_setting('assignment_date'),
                           gift_limit=get_gift_limit(),
                           comments=comments,
                           total_members=total_members,
                           members_with_wishes=members_with_wishes)


@app.route('/my_wishlist/set_participation', methods=['POST'])
def set_participation():
    """Allow a household member to change their own Secret Santa participation."""
    member_name = request.form.get('member_name', '').strip()
    selected_members = session.get('selected_members', [])
    if not member_name or member_name not in selected_members:
        session['wish_popup'] = 'Die Wichtelteilnahme konnte nicht geändert werden.'
        return redirect(url_for('my_wishlist'))

    include_in_assignment = 1 if '1' in request.form.getlist('include_in_assignment') else 0
    conn = get_db_connection()
    conn.execute(
        'UPDATE family_members SET include_in_assignment = ? WHERE name = ?',
        (include_in_assignment, member_name)
    )
    conn.execute('DELETE FROM secret_santa')
    conn.commit()
    conn.close()
    set_setting('assignment_announcement_version', str(time.time_ns()))
    set_setting(
        'assignment_announcement_message',
        f'Die Wichtelteilnahme von {member_name} wurde '
        f'{"aktiviert" if include_in_assignment else "deaktiviert"}. '
        'Die bisherige Wichtel-Zuteilung wurde zurückgesetzt.'
    )
    session['wish_popup'] = (
        f'Die Wichtelteilnahme für {member_name} wurde '
        f'{"aktiviert" if include_in_assignment else "deaktiviert"}. '
        'Die bisherige Zuteilung wurde zurückgesetzt.'
    )
    return redirect(url_for('my_wishlist'))



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
            return render_template('admin_login.html', error='Ungültige Zugangsdaten')

    return render_template('admin_login.html')


@app.route('/set_language', methods=['POST'])
def set_language():
    """Keep the legacy endpoint compatible while German remains fixed."""
    next_url = request.form.get('next') or request.referrer or url_for('index')
    resp = make_response(redirect(next_url))
    resp.set_cookie('language', 'de', max_age=60 * 60 * 24 * 365)
    return resp


@app.route('/preview/wish')
def preview_wish():
    """Return the current preview, rotating only when explicitly requested."""
    preview = get_preview_person(rotate=request.args.get('rotate') == '1')
    if not preview:
        return jsonify({'wishes': [], 'at_limit': False})
    return jsonify({
        'person_name': preview['person_name'],
        'at_limit': preview['at_limit'],
        'wishes': [
            {'wish_text': wish['wish_text'], 'product_link': wish['product_link']}
            for wish in preview['wishes']
        ]
    })


@app.route('/comment/add', methods=['POST'])
def add_comment():
    """Add a comment to the comments section."""
    comment_text = request.form.get('comment_text', '').strip()
    author_name = request.form.get('author_name', '').strip() or None
    if comment_text:
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO comments (author_name, comment_text, created_at) VALUES (?, ?, ?)',
            (
                author_name,
                comment_text,
                datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')
            )
        )
        conn.commit()
        conn.close()
    return redirect(url_for('my_wishlist'))


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
    assignment_date = get_setting('assignment_date')
    gift_limit = get_gift_limit()
    preview_interval = get_preview_interval()
    preview_person = get_preview_person()

    return render_template('admin_panel.html', family_members=family_members,
                           secret_santa=secret_santa, all_wishes=all_wishes,
                           wish_deadline=wish_deadline,
                           assignment_date=assignment_date,
                           gift_limit=gift_limit,
                           preview_interval=preview_interval,
                           preview_person=preview_person)


@app.route('/admin/set_deadline', methods=['POST'])
@login_required
def set_deadline():
    """
    Save or clear the wish deadline date.
    """
    deadline = request.form.get('wish_deadline', '').strip()
    if deadline:
        set_setting('wish_deadline', deadline)
        flash(f'Einsendeschluss auf {deadline} gesetzt.', 'success')
    else:
        set_setting('wish_deadline', '')
        flash('Einsendeschluss entfernt – Wünsche können jederzeit hinzugefügt werden.', 'success')
    return redirect(url_for('admin_panel'))


@app.route('/admin/set_assignment_date', methods=['POST'])
@login_required
def set_assignment_date():
    """Save or clear the date shown for the planned Secret Santa assignment."""
    assignment_date = request.form.get('assignment_date', '').strip()
    set_setting('assignment_date', assignment_date)
    if assignment_date:
        flash(f'Termin der Wichtel-Zuteilung auf {assignment_date} gesetzt.', 'success')
    else:
        flash('Termin der Wichtel-Zuteilung entfernt.', 'success')
    return redirect(url_for('admin_panel'))


@app.route('/admin/set_gift_limit', methods=['POST'])
@login_required
def set_gift_limit():
    """Save the maximum number of wishes allowed per person."""
    try:
        gift_limit = max(1, int(request.form.get('gift_limit', '5')))
    except ValueError:
        flash('Das Wunschlimit muss eine positive Zahl sein.', 'error')
        return redirect(url_for('admin_panel'))
    set_setting('gift_limit', str(gift_limit))
    flash(f'Das Wunschlimit wurde auf {gift_limit} gesetzt.', 'success')
    return redirect(url_for('admin_panel'))


@app.route('/admin/set_preview_interval', methods=['POST'])
@login_required
def set_preview_interval():
    """Save the rotating sidebar preview interval."""
    try:
        interval = max(5, int(request.form.get('preview_interval', '30')))
    except ValueError:
        flash('Das Wechselintervall muss eine Zahl von mindestens 5 Sekunden sein.', 'error')
        return redirect(url_for('admin_panel'))
    set_setting('preview_interval', str(interval))
    flash(f'Das Wechselintervall wurde auf {interval} Sekunden gesetzt.', 'success')
    return redirect(url_for('admin_panel'))


@app.route('/admin/reset/wishes', methods=['POST'])
@login_required
def reset_wishes():
    """Delete all wishes."""
    conn = get_db_connection()
    conn.execute('DELETE FROM wishes')
    conn.execute("DELETE FROM settings WHERE key = 'gift_positions'")
    conn.commit()
    conn.close()
    flash('Alle Wünsche wurden zurückgesetzt.', 'success')
    return redirect(url_for('admin_panel'))


@app.route('/admin/reset/assignment', methods=['POST'])
@login_required
def reset_assignment():
    """Delete all Secret Santa assignments."""
    conn = get_db_connection()
    conn.execute('DELETE FROM secret_santa')
    conn.commit()
    conn.close()
    flash('Die Wichtel-Zuteilung wurde zurückgesetzt.', 'success')
    return redirect(url_for('admin_panel'))


@app.route('/admin/reset/comments', methods=['POST'])
@login_required
def reset_comments():
    """Delete all comments."""
    conn = get_db_connection()
    conn.execute('DELETE FROM comments')
    conn.commit()
    conn.close()
    flash('Alle Kommentare wurden zurückgesetzt.', 'success')
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
        'SELECT name, team_name FROM family_members '
        'WHERE include_in_assignment = 1 ORDER BY name ASC'
    ).fetchall()
    names = [m['name'] for m in members]
    teams = {m['name']: m['team_name'] for m in members}

    if len(names) < 2:
        flash('Für das Wichteln werden mindestens zwei Teilnehmer benötigt.', 'error')
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
            'Mit den aktuellen Team-Einschränkungen konnte keine gültige '
            'Wichtel-Zuteilung erstellt werden. Füge weitere Teilnehmer hinzu oder '
            'passe die Teamgrößen an.',
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
    set_setting('assignment_announcement_version', str(time.time_ns()))
    set_setting(
        'assignment_announcement_message',
        TRANSLATIONS['de']['assignment_notification']
    )
    conn.close()
    flash('Die Wichtel-Zuteilung wurde erfolgreich erstellt.', 'success')
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
                'INSERT INTO family_members '
                '(name, team_name, include_in_assignment) VALUES (?, ?, 1)',
                (name, team_name)
            )
            conn.commit()
            flash(f'{name} wurde zum Familienmitglieder-Pool hinzugefügt.', 'success')
        except sqlite3.IntegrityError:
            # Name already exists
            flash(f'Fehler: {name} ist bereits im Familienmitglieder-Pool vorhanden.', 'error')
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
    include_in_assignment = 1 if '1' in request.form.getlist('include_in_assignment') else 0

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
                    'UPDATE family_members SET name = ?, team_name = ?, '
                    'include_in_assignment = ? WHERE id = ?',
                    (new_name, team_name, include_in_assignment, member_id)
                )

                # Update all wishes with the old name
                conn.execute(
                    'UPDATE wishes SET person_name = ? WHERE person_name = ?',
                    (new_name, old_name)
                )

                conn.commit()
                flash(f'{old_name} wurde zu {new_name} aktualisiert.', 'success')
            except sqlite3.IntegrityError:
                # Name already exists
                flash(f'Fehler: {new_name} ist bereits im Familienmitglieder-Pool vorhanden.', 'error')

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