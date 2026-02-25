"""
Flask Web Application for Family Christmas Wish List

This application allows family members to:
- Add wishes to a shared list
- Delete wishes
- View all wishes in a simple table
- Admin can manage family members pool and run Secret Santa assignments
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
from functools import wraps
from markupsafe import Markup, escape
import random
import sqlite3
import os
from datetime import date, datetime

app = Flask(__name__)
# WARNING: Without SECRET_KEY set, a new random key is generated on every restart,
# invalidating all user sessions. Set SECRET_KEY in your environment or .env file.
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

SUPPORTED_LANGUAGES = {'en': 'English', 'de': 'Deutsch', 'ru': 'Русский'}

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
        'reset_btn': 'Alle Wünsche, Zuteilungen & Kommentare zurücksetzen',
        'reset_confirm': 'Hiermit werden ALLE Wünsche, ALLE Wichtel-Zuteilungen und ALLE Kommentare gelöscht. Bist du sicher?',
        'reset_desc': 'Dies löscht alle Wünsche, setzt die Wichtel-Zuteilungen zurück und löscht alle Kommentare.',
        'delete_member_confirm': 'Bist du sicher? Dadurch werden auch alle Wünsche für',
    },
    'ru': {
        'title': 'Семейный список пожеланий',
        'header': '🎄 Семейный список пожеланий 🎅',
        'admin': '⚙️ Админ',
        'logout': 'Выйти',
        'back_to_wishlist': '← Назад к списку',
        'change_language': '🌐 Язык',
        'language_popup_title': 'Выбери язык',
        'language_popup_desc': 'Пожалуйста, выбери предпочтительный язык:',
        'confirm_language': 'Подтвердить',
        'who_are_you': 'Кто ты?',
        'select_name': 'Выбери своё имя, чтобы увидеть свой список пожеланий.',
        'select_members': '🎁 Выбери своё имя:',
        'team_restriction_hint': 'Подсказка: Выбрав участника из команды, ты сможешь добавить только других участников той же команды.',
        'different_team_error': 'Можно выбирать только участников одной команды.',
        'view_wishlist': '🎅 Посмотреть мой список',
        'no_members': 'Участников ещё нет. Попроси администратора добавить участников! 👨‍👩‍👧‍👦',
        'please_select': 'Пожалуйста, выбери хотя бы одного участника.',
        'my_wishlist': '🎁 Мой список пожеланий',
        'viewing_as': 'Просмотр как:',
        'secret_santa': 'Тайный Санта:',
        'buys_for': '→ покупает для',
        'no_assignments': 'Жеребьёвка ещё не проведена. Попроси администратора запустить жеребьёвку!',
        'wishes_closed': 'Список пожеланий закрыт.',
        'deadline_was': 'Крайний срок был',
        'no_new_wishes': 'Новые пожелания добавлять нельзя — список только для чтения.',
        'add_wish': 'Добавить пожелание',
        'add_wish_desc': 'Ты можешь добавить пожелание для себя или от имени другого участника.',
        'for_label': 'Для:',
        'select_name_opt': 'Выбери имя',
        'you_suffix': '(ты)',
        'wish_required': 'Пожелание (обязательно):',
        'product_link_label': 'Ссылка на товар (необязательно):',
        'add_wish_btn': 'Добавить',
        'your_wishes': 'Твои пожелания',
        'wishes_label': ' — пожелания',
        'no_wishes_for': 'Пожеланий ещё нет для',
        'buying_for': 'Ты покупаешь для',
        'buying_for_icon': '🛍️',
        'delete': 'Удалить',
        'delete_wish_confirm': 'Ты уверен, что хочешь удалить это пожелание?',
        'progress_label': 'участников уже добавили пожелание',
        'days_left': 'дней до крайнего срока',
        'deadline_passed': 'Срок истёк',
        'no_deadline': 'Срок не установлен',
        'comments': '💬 Комментарии',
        'add_comment': 'Добавить комментарий',
        'comment_text': 'Комментарий:',
        'your_name_label': 'Твоё имя (необязательно, оставь пустым для анонима):',
        'post_comment': 'Опубликовать',
        'anonymous': 'Аноним',
        'no_comments': 'Комментариев ещё нет. Будь первым!',
        'admin_title': 'Админ - Управление участниками',
        'wish_deadline_section': '📅 Крайний срок',
        'deadline_desc': 'После этой даты список пожеланий становится доступным только для чтения.',
        'deadline_inclusive': 'Дата крайнего срока (включительно):',
        'save_deadline': 'Сохранить срок',
        'current_deadline': 'Текущий срок:',
        'no_deadline_set': 'Срок не установлен — пожелания можно добавлять в любое время.',
        'add_member': 'Добавить участника',
        'member_name': 'Имя участника:',
        'team_optional': 'Команда (необязательно, напр. "Команда А"):',
        'no_team': 'Оставь пустым, если нет команды',
        'add_member_btn': 'Добавить участника',
        'family_pool': 'Список участников',
        'no_members_yet': 'Участников ещё нет. Добавь первого выше! 👨‍👩‍👧‍👦',
        'name_col': 'Имя',
        'team_col': 'Команда',
        'actions_col': 'Действия',
        'update_btn': 'Обновить',
        'secret_santa_admin': '🎅 Жеребьёвка Тайного Санты',
        'run_ss': 'Провести жеребьёвку',
        'run_ss_confirm': 'Это перезапишет текущую жеребьёвку. Продолжить?',
        'giver': 'Даритель',
        'receiver': '→ Покупает для',
        'no_ss': 'Жеребьёвка ещё не проводилась. Нажми "Провести жеребьёвку".',
        'all_wishes': '📋 Все пожелания',
        'person_col': 'Участник',
        'wish_col': 'Пожелание',
        'product_col': 'Ссылка на товар',
        'view_product': 'Смотреть товар',
        'no_wishes_admin': 'Пожеланий ещё нет.',
        'reset_section': '🔄 Сброс',
        'reset_btn': 'Сбросить все пожелания, жеребьёвку и комментарии',
        'reset_confirm': 'Это удалит ВСЕ пожелания, ВСЮ жеребьёвку и ВСЕ комментарии. Ты уверен?',
        'reset_desc': 'Удаляет все пожелания, сбрасывает жеребьёвку и удаляет все комментарии.',
        'delete_member_confirm': 'Ты уверен? Это также удалит все пожелания для',
    },
}


@app.template_filter('nl2br')
def nl2br_filter(value):
    """Convert newlines in text to HTML <br> tags, safely escaping HTML."""
    return Markup(escape(value).replace('\n', Markup('<br>\n')))


def get_language():
    """Return current language code from cookie, defaulting to 'en'."""
    lang = request.cookies.get('language', '')
    return lang if lang in SUPPORTED_LANGUAGES else 'en'


@app.context_processor
def inject_translations():
    """Inject translation dict and language info into every template."""
    lang = get_language()
    return {
        't': TRANSLATIONS[lang],
        'lang': lang,
        'supported_languages': SUPPORTED_LANGUAGES,
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

    # Gather comments
    conn2 = get_db_connection()
    comments = conn2.execute(
        'SELECT * FROM comments ORDER BY id DESC'
    ).fetchall()
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
                           comments=comments,
                           total_members=total_members,
                           members_with_wishes=members_with_wishes)



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


@app.route('/set_language', methods=['POST'])
def set_language():
    """Set the preferred language via cookie and redirect back."""
    lang = request.form.get('language', 'en')
    if lang not in SUPPORTED_LANGUAGES:
        lang = 'en'
    next_url = request.form.get('next') or request.referrer or url_for('index')
    resp = make_response(redirect(next_url))
    resp.set_cookie('language', lang, max_age=60 * 60 * 24 * 365)
    return resp


@app.route('/comment/add', methods=['POST'])
def add_comment():
    """Add a comment to the comments section."""
    comment_text = request.form.get('comment_text', '').strip()
    author_name = request.form.get('author_name', '').strip() or None
    if comment_text:
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO comments (author_name, comment_text, created_at) VALUES (?, ?, ?)',
            (author_name, comment_text, datetime.utcnow().strftime('%Y-%m-%d %H:%M'))
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


@app.route('/admin/reset', methods=['POST'])
@login_required
def admin_reset():
    """
    Reset all wishes, Secret Santa assignments, and comments.
    """
    conn = get_db_connection()
    conn.execute('DELETE FROM wishes')
    conn.execute('DELETE FROM secret_santa')
    conn.execute('DELETE FROM comments')
    conn.commit()
    conn.close()
    flash('All wishes, Secret Santa assignments, and comments have been reset.', 'success')
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
