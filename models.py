from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
db = SQLAlchemy()

class Learner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    gender = db.Column(db.String(10))
    age = db.Column(db.Integer, nullable=False)
    emergency_contact = db.Column(db.String(15), nullable=False)
    current_grade = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Boolean, default=False)

    bookings = db.relationship('Booking', back_populates='learner', cascade="all, delete-orphan")
    reviews = db.relationship('Review', back_populates='learner', cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
class Coach(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    lessons = db.relationship('Lesson', back_populates='coach')
    @property
    def reviews(self):
        return [review for lesson in self.lessons for review in lesson.reviews]

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    day_of_week = db.Column(db.String(10), nullable=False)  
    time_slot = db.Column(db.String(10), nullable=False)    
    grade_level = db.Column(db.Integer, nullable=False)     
    max_capacity = db.Column(db.Integer, default=4)

    coach_id = db.Column(db.Integer, db.ForeignKey('coach.id'), nullable=False)
    coach = db.relationship('Coach', back_populates='lessons')

    bookings = db.relationship('Booking', back_populates='lesson', cascade="all, delete-orphan")
    reviews = db.relationship('Review', back_populates='lesson', cascade="all, delete-orphan")

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    learner_id = db.Column(db.Integer, db.ForeignKey('learner.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    status = db.Column(db.String(10), default='booked')  

    learner = db.relationship('Learner', back_populates='bookings')
    lesson = db.relationship('Lesson', back_populates='bookings')

    __table_args__ = (db.UniqueConstraint('learner_id', 'lesson_id', name='_learner_lesson_uc'),)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    learner_id = db.Column(db.Integer, db.ForeignKey('learner.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False) 
    comment = db.Column(db.Text)

    learner = db.relationship('Learner', back_populates='reviews')
    lesson = db.relationship('Lesson', back_populates='reviews')

