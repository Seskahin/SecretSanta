# Family Christmas Wish List

A minimal Flask web application for managing a family Christmas wish list.

## Features

- **Family Members Pool**: Manage a database of family members who can have wishes
- **Admin Panel**: Secure admin interface with basic authentication to manage family members
- **Add Wishes**: Add wishes for family members with wish text and optional product link
- **Grouped Display**: View wishes organized by family member in separate tables
- **Reserve Wishes**: Mark wishes as reserved to let others know you're handling them
- **Delete Wishes**: Remove wishes from the list
- **Automatic SQLite Database**: Database is created automatically on first run
- **Simple and Clean Interface**: Easy-to-use interface with responsive design

## Requirements

- Python 3.7+
- Flask 3.0.0

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

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
   - Click "Admin Panel" button on the homepage
   - Login with default credentials:
     - Username: `admin`
     - Password: `admin123`
   - Add family members to the pool
   - Go back to the homepage

4. **Adding Wishes**:
   - Select a family member from the dropdown
   - Enter the wish text
   - Optionally add a product link
   - Click "Add Wish"

5. **Managing Wishes**:
   - Reserve wishes by clicking the "Reserve" button
   - Unreserve by clicking "Unreserve"
   - Delete wishes by clicking the "Delete" button

6. **Admin Management**:
   - Access admin panel to add, edit, or delete family members
   - Deleting a family member will also delete all their wishes

## Project Structure

```
/SecretSanta
    app.py              # Main Flask application
    requirements.txt    # Python dependencies
    wishlist.db         # SQLite database (created automatically)
    /templates
        base.html       # Base template with styling
        index.html      # Main page template
```

## Database Schema

The application uses a SQLite database with the following schema:

### Family Members Table
```sql
CREATE TABLE family_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
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

## Security Notes

- **Admin Credentials**: The default admin credentials (admin/admin123) are hardcoded for simplicity
- **Production Use**: For production deployment:
  - Change the `app.secret_key` in `app.py`
  - Use environment variables for admin credentials
  - Implement password hashing (e.g., using bcrypt)
  - Use HTTPS and a production WSGI server like gunicorn
  - Consider adding CSRF protection