from flask import Flask, render_template, request, redirect, url_for, session, flash, get_flashed_messages
from flask_bcrypt import Bcrypt
from models import db, bcrypt, Learner, Coach, Lesson, Booking, Review
from config import Config
from datetime import date

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
bcrypt = Bcrypt(app)
app.secret_key = "a" #this would be a unique key for each user if being properly deployed

# Home Page
@app.route("/")
def home():
    num_learners = Learner.query.filter_by(is_admin=False).count()  # Exclude admins
    num_coaches = Coach.query.count()
    num_lessons = Lesson.query.count()
    return render_template("home.html", 
                           num_learners=num_learners, 
                           num_coaches=num_coaches, 
                           num_lessons=num_lessons)


# Signup Route
@app.route("/signup", methods=["GET", "POST"])
def signup():
    message = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        name = request.form["name"]
        gender = request.form["gender"]
        age = int(request.form["age"])
        emergency_contact = request.form["emergency_contact"]
        current_grade = int(request.form.get("current_grade", 0))

        if not (4 <= age <= 11):
            message = "Age must be between 4 and 11."
        elif Learner.query.filter_by(username=username).first():
            message = "Username already taken."
        else:
            learner = Learner(
                username=username,
                name=name,
                gender=gender,
                age=age,
                emergency_contact=emergency_contact,
                current_grade=current_grade
            )
            learner.set_password(password)
            db.session.add(learner)
            db.session.commit()
            message = f"Learner {name} registered successfully!"
    return render_template("signup.html", message=message)

# Login Route
@app.route("/login", methods=["GET", "POST"])
def login():
    message = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        learner = Learner.query.filter_by(username=username).first()
        if learner and learner.check_password(password): 
            session['user_id'] = learner.id
            session['is_admin'] = learner.is_admin

            message = f"Logged in as {learner.name}"
            return redirect(url_for('calendar'))
        else:
            message = "Invalid username or password."
    
    return render_template("login.html", message=message)



# Account Page
@app.route("/account")
def account():
    user_id = session.get('user_id')

    if not user_id:
        flash("You must be logged in to view your account.", "error")
        return redirect(url_for('login'))

    learner = Learner.query.get(user_id)

    if learner is None:
        flash("Learner not found. Please log in again.", "error")
        session.pop('user_id', None)
        session.pop('is_admin', None)
        return redirect(url_for('login'))

    bookings = Booking.query.filter_by(learner_id=learner.id).all()

    return render_template("account.html", learner=learner, bookings=bookings)


@app.route("/calendar")
def calendar():
    filter_type = request.args.get("filter_type")
    filter_value = request.args.get("filter_value")

    query = Lesson.query

    if filter_type == "day" and filter_value:
        query = query.filter_by(day_of_week=filter_value)
    elif filter_type == "grade" and filter_value.isdigit():
        query = query.filter_by(grade_level=int(filter_value))
    elif filter_type == "coach" and filter_value:
        query = query.join(Lesson.coach).filter(Coach.name == filter_value)

    lessons = query.all()
    return render_template(
        "calendar.html",
        lessons=lessons,
        filter_type=filter_type,
        filter_value=filter_value
    )


# Booking a Lesson
@app.route("/book_lesson/<int:lesson_id>", methods=["POST"])
def book_lesson(lesson_id):
    if 'user_id' not in session:
        flash("You must be logged in to book a lesson.", "error")
        return redirect(url_for('login'))

    learner = Learner.query.get(session['user_id'])
    lesson = Lesson.query.get_or_404(lesson_id)

    if lesson.grade_level < learner.current_grade or lesson.grade_level > learner.current_grade + 1:
        flash("You can only book lessons for your current grade or one level higher.", "error")
        return redirect(url_for('calendar'))

    existing = Booking.query.filter_by(learner_id=learner.id, lesson_id=lesson.id).first()
    if existing:
        flash("You have already booked this lesson.", "error")
        return redirect(url_for('calendar'))

    if len(lesson.bookings) >= lesson.max_capacity:
        flash("Lesson is full.", "error")
        return redirect(url_for('calendar'))

    booking = Booking(learner_id=learner.id, lesson_id=lesson.id, status='booked')
    db.session.add(booking)
    db.session.commit()
    flash("Lesson booked successfully!", "success")
    return redirect(url_for('calendar'))

# Cancel booking
@app.route("/cancel_booking/<int:booking_id>", methods=["POST"])
def cancel_booking(booking_id):
    if 'user_id' not in session:
        flash("You must be logged in to cancel a booking.", "error")
        return redirect(url_for('login'))

    booking = Booking.query.get_or_404(booking_id)

    if booking.learner_id != session['user_id']:
        flash("You cannot cancel someone else's booking.", "error")
        return redirect(url_for('account'))

    db.session.delete(booking)
    db.session.commit()

    flash("Booking cancelled successfully!", "success")
    return redirect(url_for('account'))

# Attendance Page (Admin)
@app.route("/attendance", methods=["GET", "POST"])
def attendance():
    if not session.get('is_admin'):
        flash("You must be an admin to access attendance.", "error")
        return redirect(url_for('login'))

    lessons = Lesson.query.order_by(Lesson.date).all()
    learners = None
    selected_lesson = None

    if request.method == "POST":
        lesson_id = request.form.get("lesson_id")
        selected_lesson = Lesson.query.get(lesson_id)
        learners = Booking.query.filter_by(lesson_id=lesson_id).all()

    return render_template("attendance.html", lessons=lessons, learners=learners, selected_lesson=selected_lesson)

# Mark Attendance Page (Admin)
@app.route("/mark_attendance", methods=["POST"])
def mark_attendance():
    if not session.get('is_admin'):
        flash("You must be an admin to perform this action.", "error")
        return redirect(url_for('login'))

    lesson_id = request.form.get("lesson_id")
    attended_ids = request.form.getlist("attended_ids")

    bookings = Booking.query.filter_by(lesson_id=lesson_id).all()
    for booking in bookings:
        if str(booking.id) in attended_ids:
            booking.status = 'attended'
            if booking.lesson.grade_level == booking.learner.current_grade + 1:
                booking.learner.current_grade += 1
        else:
            if booking.status == 'attended':
                booking.status = 'booked'

    db.session.commit()
    flash("Attendance updated successfully!", "success")
    return redirect(url_for('attendance'))

# Submit Review (Learner)
@app.route("/review/<int:booking_id>", methods=["GET", "POST"])
def submit_review(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    message = None

    existing_review = Review.query.filter_by(
        learner_id=booking.learner_id,
        lesson_id=booking.lesson_id
    ).first()

    if existing_review:
        flash("You have already submitted a review for this lesson.", "error")
        return redirect(url_for('account'))

    if request.method == "POST":
        rating = int(request.form["rating"])
        comment = request.form["comment"]

        review = Review(
            learner_id=booking.learner_id,
            lesson_id=booking.lesson_id,
            rating=rating,
            comment=comment
        )
        db.session.add(review)
        db.session.commit()
        flash("Review submitted successfully!", "success")
        return redirect(url_for('account'))

    return render_template("submit_review.html", booking=booking)


# Reports
@app.route("/reports/learners")
def learner_report():
    if not session.get('is_admin'):
        flash("You must be an admin to access learner reports.", "error")
        return redirect(url_for('login'))
    learners = Learner.query.filter_by(is_admin=False).all()
    return render_template("learner_report.html", learners=learners)


@app.route("/reports/coaches")
def coach_report():
    if not session.get('is_admin'):
        flash("You must be an admin to access coach reports.", "error")
        return redirect(url_for('login'))
    coaches = Coach.query.all()
    return render_template("coach_report.html", coaches=coaches)

# Lesson reviews
@app.route("/lesson_reviews")
def lesson_reviews():
    lessons = Lesson.query.join(Lesson.reviews).group_by(Lesson.id).order_by(Lesson.date, Lesson.time_slot).all()
    
    return render_template("lesson_reviews.html", lessons=lessons)



# Run App
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
