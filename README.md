# HJSS Summer Project

A Flask-based booking application designed to manage bookings, user accounts, timetables, attendance, reviews, and reports for learners and coaches.

# Features
- Timetable & Calendar: View and manage schedules easily.
- Reviews & Feedback: Learners can leave reviews for sessions.
- Login system: Learner can create profiles.

### Admin Features
- View all learners and their prior bookings.
- Access detailed reports

# Technology Stack
- **Backend** Python, Flask, Flask-SQLAlchemy
- **Frontend** HTML, Jinja2, Bootstrap 5
- **Database** SQLite
- **Authentication** hashed passwords within a Flask session
- **Deployment** Local server

# Requirements

- python 3.10+
- pip

# Installation: 
- Install the required packages:
```bash
pip install Flask Flask-SQLAlchemy Bcrypt
```
# Running the App
Start the Flask server by running:
python main.py.
Then navigate to http://localhost:5000 in your browser to access the application.

# Option Enhancements
- Add environment variables for secret keys and database URIs.



