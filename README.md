# Family Christmas Wish List

A minimal Flask web application for managing a family Christmas wish list with Secret Santa assignments.

## Features

- **Family Members Pool**: Manage a database of family members who can have wishes
- **Admin Panel**: Secure admin interface with basic authentication to manage family members
- **Add Wishes**: Add wishes for family members with wish text and optional product link
- **Grouped Display**: View wishes organized by family member in separate tables
- **Delete Wishes**: Remove wishes from the list
- **Secret Santa Assignments**: Automatically assign Secret Santa givers/receivers
- **German Interface**: The application is displayed in German
- **Wish Deadline**: Set a date after which the wish list becomes read-only
- **Assignment Date**: Configure a date shown as a Secret Santa countdown; the assignment remains manual
- **Assignment Participation**: Enable or exclude individual family members from Secret Santa
- **Comments**: Leave comments on the wish list
- **Separate Resets**: Reset wishes, the Secret Santa assignment, or comments independently
- **Persistent Identity**: The selected household members remain stored for ten years
- **Wish Limit**: Configure the maximum number of wishes per person in the admin panel
- **Wish Preview**: A rotating preview shows wishes without revealing the person's name
- **Gift Decorations**: Randomly selected gift images decorate both sides of the page
- **Persistent Gift Placement**: Existing gifts keep their position, size, rotation, and image across page reloads; only newly added wishes receive new decorations
- **Automatic SQLite Database**: Database is created automatically on first run
- **Simple and Clean Interface**: Easy-to-use interface with responsive design

## Requirements

- Python 3.9+
- The exact Python package versions are listed in `requirements.txt`

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file from the example and set your values:
```bash
cp .env.example .env
# Edit .env and set SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD
```

## Configuration (Environment Variables)

The application is configured via environment variables. Copy `.env.example` to `.env` and adjust the values:

| Variable | Description | Default (dev only) |
|---|---|---|
| `SECRET_KEY` | Flask session secret key | random (changes on restart) |
| `ADMIN_USERNAME` | Admin panel username | `admin` |
| `ADMIN_PASSWORD` | Admin panel password | `admin123` |

> **Important**: Always set `SECRET_KEY`, `ADMIN_USERNAME`, and `ADMIN_PASSWORD` to strong, unique values before deploying or sharing access.

## Usage

1. Run the application:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://127.0.0.1:5000
```

3. **Admin Setup** (First Time):
   - Click "Admin" button on the homepage
   - Login with the credentials set in your `.env` file (default: `admin` / `admin123`)
   - Add family members to the pool
   - Optionally set a wish deadline
   - Run Secret Santa assignments

4. **Adding Wishes**:
   - Select your name on the homepage
   - Enter a wish text
   - Optionally add a product link
   - Click "Add Wish"

5. **Managing Wishes**:
   - Delete wishes by clicking the "Delete" button

6. **Secret Santa**:
   - Admin can run Secret Santa assignments from the admin panel
   - Each family member sees only their own assignment

## Date and time behavior

The application stores deadlines and the planned Secret Santa assignment as dates
(`YYYY-MM-DD`), not as times. Countdown timers are calculated in the visitor's
browser using the browser's local time zone. Therefore, a countdown can differ
between devices if their time zone or system clock differs.

The server validates whether the wish deadline has passed using the VM's local
date (`date.today()`). Configure the VM's time zone and system clock correctly
for the location where the application is operated. For a German household,
the VM should normally use `Europe/Berlin`, including automatic daylight-saving
time.

Comments are stored internally with a UTC timestamp and displayed in German
local time (`Europe/Berlin`), including automatic daylight-saving time.

## Project Structure

```
/SecretSanta
    app.py              # Main Flask application
    requirements.txt    # Python dependencies
    .env.example        # Example environment variable configuration
    wishlist.db         # SQLite database (created automatically, not committed)
    /templates
        base.html           # Base template with styling
        index.html          # Main page template
        who_are_you.html    # Name selection page
        my_wishlist.html    # Personal wishlist page
        admin_login.html    # Admin login page
        admin_panel.html    # Admin management page
```

## Database Schema

The application uses a SQLite database with the following schema:

### Family Members Table
```sql
CREATE TABLE family_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    team TEXT  -- optional grouping label (e.g. "Team A") used for Secret Santa constraints
);
```

### Wishes Table
```sql
CREATE TABLE wishes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_name TEXT NOT NULL,
    wish_text TEXT NOT NULL,
    product_link TEXT,
    reserved INTEGER DEFAULT 0
);
```

### Secret Santa Table
```sql
CREATE TABLE secret_santa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    giver_name TEXT NOT NULL,
    receiver_name TEXT NOT NULL
);
```

## Security Notes

- **Secret Key**: `SECRET_KEY` is used to sign Flask sessions. Always set a strong, random value in production.
- **Admin Credentials**: Set `ADMIN_USERNAME` and `ADMIN_PASSWORD` via environment variables — never use the defaults in production.
- **Production Deployment**:
  - Use a production WSGI server like [gunicorn](https://gunicorn.org/)
  - Serve behind HTTPS (e.g., with nginx + Let's Encrypt)
  - Consider adding CSRF protection
  - Consider password hashing (e.g., using `werkzeug.security`)