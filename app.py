import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'smart-study-planner-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    study_goals = db.Column(db.Text, nullable=True)
    available_hours = db.Column(db.Float, default=4.0)
    tasks = db.relationship('Task', backref='user', lazy=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    deadline = db.Column(db.Date, nullable=False)
    difficulty = db.Column(db.String(20), default='medium') # easy, medium, hard
    priority = db.Column(db.Integer, default=1) # 1-high, 2-medium, 3-low
    completed = db.Column(db.Boolean, default=False)
    estimated_hours = db.Column(db.Float, default=1.0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    scheduled_date = db.Column(db.Date, nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Auth Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Username already exists!')
            return redirect(url_for('register'))
        
        new_user = User(username=username, password=generate_password_hash(password, method='pbkdf2:sha256'))
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# App Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    today = datetime.now().date()
    today_tasks = Task.query.filter_by(user_id=current_user.id, scheduled_date=today).all()
    all_tasks = Task.query.filter_by(user_id=current_user.id).all()
    
    completed_count = sum(1 for t in all_tasks if t.completed)
    pending_count = len(all_tasks) - completed_count
    progress = (completed_count / len(all_tasks) * 100) if all_tasks else 0
    
    # Motivational message
    messages = [
        "Believe you can and you're halfway there.",
        "Success is the sum of small efforts, repeated day in and day out.",
        "The only way to do great work is to love what you do.",
        "Your future depends on what you do today."
    ]
    import random
    motivational_msg = random.choice(messages)
    
    return render_template('dashboard.html', 
                           tasks=today_tasks, 
                           progress=progress, 
                           completed=completed_count, 
                           pending=pending_count,
                           message=motivational_msg)

@app.route('/add_task', methods=['POST'])
@login_required
def add_task():
    data = request.form
    new_task = Task(
        subject=data.get('subject'),
        title=data.get('title'),
        deadline=datetime.strptime(data.get('deadline'), '%Y-%m-%d').date(),
        difficulty=data.get('difficulty'),
        priority=int(data.get('priority')),
        estimated_hours=float(data.get('estimated_hours', 1.0)),
        user_id=current_user.id
    )
    db.session.add(new_task)
    db.session.commit()
    flash('Task added successfully!')
    return redirect(url_for('dashboard'))

@app.route('/complete_task/<int:task_id>')
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id == current_user.id:
        task.completed = not task.completed
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/generate_plan')
@login_required
def generate_plan():
    """
    Smart Logic:
    1. Sort by Deadline (earliest first)
    2. Sort by Priority (1 is highest)
    3. Sort by Difficulty (hard first)
    4. Distribute tasks based on available hours per day
    """
    tasks = Task.query.filter_by(user_id=current_user.id, completed=False).all()
    
    # Sort: Deadline (asc), Priority (asc), Difficulty (hard -> medium -> easy)
    diff_map = {'hard': 0, 'medium': 1, 'easy': 2}
    tasks.sort(key=lambda x: (x.deadline, x.priority, diff_map.get(x.difficulty, 1)))
    
    today = datetime.now().date()
    current_date = today
    daily_hours_limit = current_user.available_hours or 4.0
    accumulated_hours = 0
    
    for task in tasks:
        # If adding this task exceeds daily limit, move to next day
        # Exception: if it's the first task of the day and exceeds limit, still keep it but it's the only one
        if accumulated_hours + task.estimated_hours > daily_hours_limit and accumulated_hours > 0:
            current_date += timedelta(days=1)
            accumulated_hours = 0
            
        task.scheduled_date = current_date
        accumulated_hours += task.estimated_hours
        
        # Ensure we don't schedule tasks before today
        if task.scheduled_date < today:
            task.scheduled_date = today
            
    db.session.commit()
    flash('Smart Study Plan Generated! Tasks distributed based on difficulty and deadlines.')
    return redirect(url_for('dashboard'))

@app.route('/api/recommendations')
@login_required
def get_recommendations():
    tasks = Task.query.filter_by(user_id=current_user.id, completed=False).all()
    recs = []
    
    hard_tasks = [t for t in tasks if t.difficulty == 'hard']
    if hard_tasks:
        recs.append(f"💡 You have {len(hard_tasks)} 'Hard' tasks. Tackle them when your energy is highest!")
    
    today = datetime.now().date()
    urgent_tasks = [t for t in tasks if t.deadline <= today + timedelta(days=2)]
    if urgent_tasks:
        recs.append(f"⏰ {len(urgent_tasks)} tasks are due very soon. Prioritize these!")
        
    if not tasks:
        recs.append("🌟 All caught up! Time for a well-deserved break.")
    elif len(recs) < 2:
        recs.append("📈 Consistency is key. Keep following your generated plan!")
        
    return jsonify(recs)

@app.route('/api/stats')
@login_required
def get_stats():
    # Mock data for demonstration - in a real app, we'd query historical completion data
    return jsonify({"labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], "data": [2, 4, 3, 5, 2, 0, 0]})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
