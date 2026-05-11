"""
RST Library Backend - Flask Application
A complete library management system with books, events, and user management
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# Database Configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'rst_library'),
    'charset': 'utf8mb4',
    'use_unicode': True,
    'autocommit': True
}

CORS(app, resources={r'/api/*': {
    'origins': '*',
    'methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    'allow_headers': ['Content-Type', 'Authorization']
}}, supports_credentials=True)

# ==================== Database Functions ====================

def get_db_connection():
    """Get database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def query_db(query, args=(), one=False):
    """Execute a query and return results"""
    try:
        connection = get_db_connection()
        if not connection:
            return None if one else []
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, args)
        result = cursor.fetchall()
        cursor.close()
        connection.close()
        
        return (result[0] if result else None) if one else result
    except Error as e:
        print(f"Database query error: {e}")
        return None if one else []

def execute_db(query, args=()):
    """Execute a query and commit"""
    try:
        connection = get_db_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        cursor.execute(query, args)
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except Error as e:
        print(f"Database execution error: {e}")
        return False

# ==================== Authentication ====================

def token_required(f):
    """Decorator to require user session"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = request.headers.get('X-User-ID')
        
        if not user_id:
            return jsonify({'message': 'User ID is missing'}), 401
        
        try:
            user_id = int(user_id)
        except ValueError:
            return jsonify({'message': 'Invalid user ID'}), 401
        
        return f(user_id, *args, **kwargs)
    
    return decorated

# ==================== User Routes ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ['fullName', 'email', 'studentId', 'password']):
        return jsonify({'message': 'Missing required fields'}), 400
    
    fullName = data['fullName']
    email = data['email']
    studentId = data['studentId']
    password = data['password']
    
    # Check if user exists
    existing = query_db('SELECT * FROM users WHERE email = ? OR studentId = ?', 
                       (email, studentId), one=True)
    if existing:
        return jsonify({'message': 'User already exists'}), 409
    
    # Hash password and create user
    hashed_password = generate_password_hash(password)
    try:
        execute_db('INSERT INTO users (fullName, email, studentId, password) VALUES (%s, %s, %s, %s)',
                  (fullName, email, studentId, hashed_password))
        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        return jsonify({'message': f'Registration failed: {str(e)}'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user and return user info"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ['email', 'password']):
        return jsonify({'message': 'Missing email or password'}), 400
    
    email = data['email']
    password = data['password']
    
    user = query_db('SELECT * FROM users WHERE email = %s', (email,), one=True)
    
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'message': 'Invalid email or password'}), 401
    
    return jsonify({
        'message': 'Login successful',
        'user': {
            'id': user['id'],
            'fullName': user['fullName'],
            'email': user['email'],
            'studentId': user['studentId']
        }
    }), 200

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout user (client-side token deletion)"""
    return jsonify({'message': 'Logout successful'}), 200

@app.route('/api/users/<int:user_id>', methods=['GET'])
@token_required
def get_user(current_user_id, user_id):
    """Get user profile"""
    if current_user_id != user_id:
        return jsonify({'message': 'Unauthorized'}), 403
    
    user = query_db('SELECT id, fullName, email, studentId, memberSince FROM users WHERE id = %s',
                   (user_id,), one=True)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    return jsonify(user), 200

# ==================== Book Routes ====================

@app.route('/api/books', methods=['GET'])
def get_books():
    """Get all books with optional category filter"""
    category = request.args.get('category')
    
    if category and category != 'All':
        books = query_db('''
            SELECT id, title, author, category, description, coverImage, addedDate
            FROM books
            WHERE category = %s
            ORDER BY id
        ''', (category,))
    else:
        books = query_db('''
            SELECT id, title, author, category, description, coverImage, addedDate
            FROM books
            ORDER BY id
        ''')
    
    return jsonify(books), 200

@app.route('/api/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    """Get a single book"""
    book = query_db('''
        SELECT id, title, author, category, description, coverImage, addedDate
        FROM books
        WHERE id = %s
    ''', (book_id,), one=True)
    
    if not book:
        return jsonify({'message': 'Book not found'}), 404
    
    return jsonify(book), 200

@app.route('/api/books/search', methods=['GET'])
def search_books():
    """Search books by title or author"""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'message': 'Search query required'}), 400
    
    books = query_db('''
        SELECT id, title, author, category, description, coverImage, addedDate
        FROM books
        WHERE title LIKE %s OR author LIKE %s
        ORDER BY id
    ''', (f'%{query}%', f'%{query}%'))
    
    return jsonify(books), 200

# ==================== Event Routes ====================

@app.route('/api/events', methods=['GET'])
def get_events():
    """Get all events"""
    events = query_db('''
        SELECT id, title, date, time, location, description
        FROM events
        ORDER BY date
    ''')
    
    return jsonify(events), 200

@app.route('/api/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    """Get a single event"""
    event = query_db('''
        SELECT id, title, date, time, location, description
        FROM events
        WHERE id = %s
    ''', (event_id,), one=True)
    
    if not event:
        return jsonify({'message': 'Event not found'}), 404
    
    return jsonify(event), 200

@app.route('/api/events/<int:event_id>/register', methods=['POST'])
@token_required
def register_event(current_user_id, event_id):
    """Register user for an event"""
    # Check if event exists
    event = query_db('SELECT * FROM events WHERE id = %s', (event_id,), one=True)
    if not event:
        return jsonify({'message': 'Event not found'}), 404
    
    # Check if already registered
    existing = query_db('SELECT * FROM user_events WHERE user_id = %s AND event_id = %s',
                       (current_user_id, event_id), one=True)
    if existing:
        return jsonify({'message': 'Already registered for this event'}), 409
    
    # Register user
    if execute_db('INSERT INTO user_events (user_id, event_id) VALUES (%s, %s)',
                  (current_user_id, event_id)):
        return jsonify({'message': 'Registered successfully'}), 201
    else:
        return jsonify({'message': 'Registration failed'}), 500

@app.route('/api/events/<int:event_id>/unregister', methods=['POST'])
@token_required
def unregister_event(current_user_id, event_id):
    """Unregister user from an event"""
    if execute_db('DELETE FROM user_events WHERE user_id = %s AND event_id = %s',
                  (current_user_id, event_id)):
        return jsonify({'message': 'Unregistered successfully'}), 200
    else:
        return jsonify({'message': 'Unregistration failed'}), 500

# ==================== Favorites Routes ====================

@app.route('/api/favorites', methods=['GET'])
@token_required
def get_favorites(current_user_id):
    """Get user's favorite books"""
    favorites = query_db('''
        SELECT b.id, b.title, b.author, b.category, b.description, b.coverImage, b.addedDate
        FROM books b
        JOIN user_favorites uf ON b.id = uf.book_id
        WHERE uf.user_id = %s
        ORDER BY b.id
    ''', (current_user_id,))
    
    return jsonify(favorites), 200

@app.route('/api/favorites/<int:book_id>', methods=['POST'])
@token_required
def add_favorite(current_user_id, book_id):
    """Add book to favorites"""
    # Check if book exists
    book = query_db('SELECT * FROM books WHERE id = %s', (book_id,), one=True)
    if not book:
        return jsonify({'message': 'Book not found'}), 404
    
    # Check if already favorited
    existing = query_db('SELECT * FROM user_favorites WHERE user_id = %s AND book_id = %s',
                       (current_user_id, book_id), one=True)
    if existing:
        return jsonify({'message': 'Already in favorites'}), 409
    
    # Add to favorites
    if execute_db('INSERT INTO user_favorites (user_id, book_id) VALUES (%s, %s)',
                  (current_user_id, book_id)):
        return jsonify({'message': 'Added to favorites'}), 201
    else:
        return jsonify({'message': 'Failed to add to favorites'}), 500

@app.route('/api/favorites/<int:book_id>', methods=['DELETE'])
@token_required
def remove_favorite(current_user_id, book_id):
    """Remove book from favorites"""
    if execute_db('DELETE FROM user_favorites WHERE user_id = %s AND book_id = %s',
                  (current_user_id, book_id)):
        return jsonify({'message': 'Removed from favorites'}), 200
    else:
        return jsonify({'message': 'Failed to remove from favorites'}), 500

# ==================== Complaints Routes ====================

@app.route('/api/complaints', methods=['POST'])
@token_required
def submit_complaint(current_user_id):
    """Submit a complaint or feedback"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ['issueType', 'message']):
        return jsonify({'message': 'Missing required fields'}), 400
    
    issueType = data['issueType']
    message = data['message']
    
    if execute_db('INSERT INTO complaints (issueType, message, userId) VALUES (%s, %s, %s)',
                  (issueType, message, current_user_id)):
        return jsonify({'message': 'Complaint submitted successfully'}), 201
    else:
        return jsonify({'message': 'Failed to submit complaint'}), 500

@app.route('/api/complaints', methods=['GET'])
@token_required
def get_complaints(current_user_id):
    """Get user's complaints"""
    complaints = query_db('''
        SELECT id, issueType, message, createdAt
        FROM complaints
        WHERE userId = %s
        ORDER BY createdAt DESC
    ''', (current_user_id,))
    
    return jsonify(complaints), 200

# ==================== Static Files ====================

@app.route('/')
def serve_index():
    """Serve the main HTML file"""
    return send_from_directory('.', 'index_improved.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('.', filename)

# ==================== Error Handlers ====================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'message': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'message': 'Internal server error'}), 500

# ==================== Health Check ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'RST Library API is running'}), 200

# ==================== Main ====================

if __name__ == '__main__':
    # Development server
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_ENV') == 'development'
    )
