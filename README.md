# Family Christmas Wish List

A minimal Flask web application for managing a family Christmas wish list.

## Features

- Add wishes with person name, wish text, and optional product link
- Reserve wishes to let others know you're handling them
- Delete wishes from the list
- View all wishes in a sortable table
- Automatic SQLite database creation
- Simple and clean interface

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

3. Add wishes using the form
4. Reserve wishes by clicking the "Reserve" button
5. Delete wishes by clicking the "Delete" button

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

```sql
CREATE TABLE wishes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_name TEXT NOT NULL,
    wish_text TEXT NOT NULL,
    product_link TEXT,
    reserved INTEGER DEFAULT 0
);
```