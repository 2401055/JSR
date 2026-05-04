# Smart Study Planner 🎯

An intelligent study planner built with Flask and SQLite to help students organize their time, track progress, and get AI-based study recommendations.

## 🚀 Features

- **User System**: Secure registration and login.
- **Smart Scheduling**: Automatically distributes tasks across days based on your available study hours and task difficulty.
- **AI Recommendations**: Suggests what to study next based on deadlines and difficulty.
- **Pomodoro Timer**: Integrated 25/5 timer to keep you focused.
- **Progress Visualization**: Visual charts (Chart.js) to track your weekly completion rate.
- **Dark Mode**: Modern UI with a toggle for night owls.

## 🛠️ Tech Stack

- **Backend**: Python, Flask, Flask-SQLAlchemy, Flask-Login
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla), Bootstrap 5
- **Database**: SQLite
- **Charts**: Chart.js

## 📦 Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd smart-study-planner
   ```

2. **Install dependencies**:
   ```bash
   pip install flask flask-sqlalchemy flask-login
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Access the app**:
   Open your browser and go to `http://127.0.0.1:5000`

## 🧠 Smart Logic Explained

- **Priority Sorting**: Tasks are sorted by Deadline -> Priority -> Difficulty.
- **Workload Balancing**: The planner calculates the total estimated hours and spreads tasks so you don't exceed your daily limit.
- **Difficulty Weighting**: "Hard" tasks are prioritized earlier in the schedule when you have more energy.

## 📁 Project Structure

```text
/smart-study-planner
│── app.py              # Main Flask application & Database models
│── database.db         # SQLite database (created on first run)
│── README.md           # Instructions
│── /static
│   ├── /css
│   │   └── style.css   # Custom styles & Dark mode
│   └── /js
│       └── main.js    # Timer, Charts, & Frontend logic
└── /templates
    ├── base.html       # Layout template
    ├── login.html      # Login page
    ├── register.html   # Signup page
    └── dashboard.html  # Main application dashboard
```
