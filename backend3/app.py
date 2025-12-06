from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import extract, func
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import date, datetime, timedelta, timezone
import os


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///SMS.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.secret_key = 'your-secret-key-here-change-in-production'
@app.context_processor
def inject_date():
    """Make date and datetime available to all templates"""
    return dict(date=date, datetime=datetime)

db = SQLAlchemy(app)

# Create upload folders
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'assignments'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'submissions'), exist_ok=True)

# ==================== DECORATORS ====================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_type') != 'admin' or 'admin_id' not in session:
            flash('Please login as admin first', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'teacher_id' not in session:
            flash('Please login as teacher first', 'error')
            return redirect(url_for('teacher_login'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'student_id' not in session:
            flash('Please login as student first', 'error')
            return redirect(url_for('student_login'))
        return f(*args, **kwargs)
    return decorated_function


# ==================== All models starts from here ====================
class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Grade(db.Model):
    __tablename__ = 'grade'
    id = db.Column(db.Integer, primary_key=True)
    grade_id = db.Column(db.String(20), unique=True, nullable=True)
    name = db.Column(db.String(50), nullable=False)
    level = db.Column(db.Integer, nullable=False)
    classes = db.relationship('Classes', backref='grade', lazy=True)


class Subject(db.Model):
    __tablename__ = 'subject'
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.String(20), unique=True, nullable=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    class_subjects = db.relationship('ClassSubject', backref='subject', lazy=True)


class Classes(db.Model):
    __tablename__ = 'classes'
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.String(20), unique=True, nullable=True)
    name = db.Column(db.String(100), nullable=False)
    section = db.Column(db.String(10))
    grade_id = db.Column(db.String(20), db.ForeignKey('grade.grade_id'))
    head = db.Column(db.String(20), db.ForeignKey('teacher.teacher_id'))
    
    students = db.relationship('Student', backref='class_obj', lazy=True)
    class_subjects = db.relationship('ClassSubject', backref='class_obj', lazy=True)
    diaries = db.relationship('Diary', backref='class_obj', lazy=True)
    attendances = db.relationship('Attendance', backref='class_obj', lazy=True)
    assignments = db.relationship('Assignment', backref='class_obj', lazy=True)
    notifications = db.relationship('Notification', backref='class_obj', lazy=True)


class ClassSubject(db.Model):
    __tablename__ = 'class_subject'
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.String(20), db.ForeignKey('classes.class_id'), nullable=False)
    subject_id = db.Column(db.String(20), db.ForeignKey('subject.subject_id'), nullable=False)
    teacher_id = db.Column(db.String(20), db.ForeignKey('teacher.teacher_id'), nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('class_id', 'subject_id', name='unique_class_subject'),
    )


class Teacher(db.Model):
    __tablename__ = 'teacher'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.String(20), unique=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    status = db.Column(db.String(20), default="Active")
    phone = db.Column(db.String(15))
    
    classes_headed = db.relationship('Classes', backref='class_teacher', lazy=True)
    class_subjects = db.relationship('ClassSubject', backref='teacher', lazy=True)
    diaries = db.relationship('Diary', backref='teacher', lazy=True)
    attendances = db.relationship('Attendance', backref='teacher', lazy=True)
    assignments = db.relationship('Assignment', backref='teacher', lazy=True)
    marks = db.relationship('Marks', backref='teacher', lazy=True)
    notifications = db.relationship('Notification', backref='teacher', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    contact_info = db.Column(db.String(15), nullable=False)
    parent_name = db.Column(db.String(100), nullable=False)
    parent_phone = db.Column(db.String(15))
    date_join = db.Column(db.Date, nullable=False, default=date.today)
    class_id = db.Column(db.String(20), db.ForeignKey('classes.class_id'))
    
    attendances = db.relationship('Attendance', backref='student', lazy=True)
    marks = db.relationship('Marks', backref='student', lazy=True)
    submissions = db.relationship('Submission', backref='student', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(20), nullable=False)
    remarks = db.Column(db.String(200))
    
    student_id = db.Column(db.String(20), db.ForeignKey('student.student_id'), nullable=False)
    class_id = db.Column(db.String(20), db.ForeignKey('classes.class_id'), nullable=False)
    class_subject_id = db.Column(db.Integer, db.ForeignKey('class_subject.id'))
    teacher_id = db.Column(db.String(20), db.ForeignKey('teacher.teacher_id'), nullable=False)
    
    class_subject = db.relationship('ClassSubject', backref='attendances')
    
    __table_args__ = (
        db.UniqueConstraint('student_id', 'date', 'class_subject_id', name='unique_attendance'),
    )


class Marks(db.Model):
    __tablename__ = 'marks'
    id = db.Column(db.Integer, primary_key=True)
    exam_type = db.Column(db.String(50), nullable=False)
    marks_obtained = db.Column(db.Float, nullable=False)
    total_marks = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    remarks = db.Column(db.String(200))
    
    student_id = db.Column(db.String(20), db.ForeignKey('student.student_id'), nullable=False)
    class_subject_id = db.Column(db.Integer, db.ForeignKey('class_subject.id'), nullable=False)
    teacher_id = db.Column(db.String(20), db.ForeignKey('teacher.teacher_id'), nullable=False)
    
    class_subject = db.relationship('ClassSubject', backref='marks')
    
    @property
    def percentage(self):
        return (self.marks_obtained / self.total_marks) * 100 if self.total_marks > 0 else 0


class Assignment(db.Model):
    __tablename__ = 'assignment'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    total_marks = db.Column(db.Float, nullable=False)
    attachment_path = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    teacher_id = db.Column(db.String(20), db.ForeignKey('teacher.teacher_id'), nullable=False)
    class_id = db.Column(db.String(20), db.ForeignKey('classes.class_id'), nullable=False)
    class_subject_id = db.Column(db.Integer, db.ForeignKey('class_subject.id'), nullable=False)
    
    class_subject = db.relationship('ClassSubject', backref='assignments')
    submissions = db.relationship('Submission', backref='assignment', lazy=True, cascade='all, delete-orphan')


class Submission(db.Model):
    __tablename__ = 'submission'
    id = db.Column(db.Integer, primary_key=True)
    submission_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    submission_link = db.Column(db.String(500))
    file_path = db.Column(db.String(300))
    marks_obtained = db.Column(db.Float)
    feedback = db.Column(db.Text)
    status = db.Column(db.String(20), default="Submitted")
    graded_at = db.Column(db.DateTime)
    
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    student_id = db.Column(db.String(20), db.ForeignKey('student.student_id'), nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('assignment_id', 'student_id', name='unique_submission'),
    )


class Diary(db.Model):
    __tablename__ = 'diary'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    notes = db.Column(db.Text, nullable=False)
    homework = db.Column(db.Text)
    instructions = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    teacher_id = db.Column(db.String(20), db.ForeignKey('teacher.teacher_id'), nullable=False)
    class_id = db.Column(db.String(20), db.ForeignKey('classes.class_id'), nullable=False)
    class_subject_id = db.Column(db.Integer, db.ForeignKey('class_subject.id'))
    
    class_subject = db.relationship('ClassSubject', backref='diaries')


class Notification(db.Model):
    __tablename__ = 'notification'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_urgent = db.Column(db.Boolean, default=False)
    
    teacher_id = db.Column(db.String(20), db.ForeignKey('teacher.teacher_id'), nullable=False)
    class_id = db.Column(db.String(20), db.ForeignKey('classes.class_id'), nullable=False)

'''==============================SOCICAL CONNECT  MODEL BEGIN========================= '''
class UserProfile(db.Model):
    """Extended profile for Students, Teachers, and Alumni"""
    __tablename__ = 'user_profile'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), unique=True, nullable=False)  # student_id, teacher_id, or alumni_id
    user_type = db.Column(db.String(20), nullable=False)  # 'student', 'teacher', 'alumni'
    
    # Profile Information
    bio = db.Column(db.Text)
    headline = db.Column(db.String(200))  # Professional headline
    profile_picture = db.Column(db.String(300))
    cover_photo = db.Column(db.String(300))
    location = db.Column(db.String(100))
    website = db.Column(db.String(200))
    linkedin_url = db.Column(db.String(200))
    github_url = db.Column(db.String(200))
    
    # Privacy settings
    is_profile_public = db.Column(db.Boolean, default=True)
    show_email = db.Column(db.Boolean, default=False)
    show_phone = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    achievements = db.relationship('Achievement', backref='profile', lazy=True, cascade='all, delete-orphan')
    skills = db.relationship('Skill', backref='profile', lazy=True, cascade='all, delete-orphan')
    experiences = db.relationship('Experience', backref='profile', lazy=True, cascade='all, delete-orphan')
    hobbies = db.relationship('Hobby', backref='profile', lazy=True, cascade='all, delete-orphan')


class Alumni(db.Model):
    """Alumni who have graduated"""
    __tablename__ = 'alumni'
    id = db.Column(db.Integer, primary_key=True)
    alumni_id = db.Column(db.String(20), unique=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    stu_id=db.Column(db.String(20),unique=True,nullable=False)   #adding the student_id as 
    password_hash = db.Column(db.String(128), nullable=False)
    
    # Alumni specific info
    graduation_year = db.Column(db.Integer, nullable=False)
    degree = db.Column(db.String(100))
    major = db.Column(db.String(100))
    current_company = db.Column(db.String(200))
    current_position = db.Column(db.String(200))
    
    phone = db.Column(db.String(15))
    joined_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Achievement(db.Model):
    """Achievements and awards"""
    __tablename__ = 'achievement'
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('user_profile.id'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # Academic, Sports, Cultural, Professional, etc.
    date_achieved = db.Column(db.Date)
    issuer = db.Column(db.String(200))  # Organization/Institution that issued
    certificate_url = db.Column(db.String(300))
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Skill(db.Model):
    """Skills and expertise"""
    __tablename__ = 'skill'
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('user_profile.id'), nullable=False)
    
    name = db.Column(db.String(100), nullable=False)
    proficiency = db.Column(db.String(20))  # Beginner, Intermediate, Advanced, Expert
    category = db.Column(db.String(50))  # Technical, Soft Skills, Languages, etc.
    
    endorsements = db.relationship('SkillEndorsement', backref='skill', lazy=True, cascade='all, delete-orphan')


class SkillEndorsement(db.Model):
    """Skill endorsements from other users"""
    __tablename__ = 'skill_endorsement'
    id = db.Column(db.Integer, primary_key=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill.id'), nullable=False)
    endorser_id = db.Column(db.String(20), nullable=False)  # user_id who endorsed
    endorser_type = db.Column(db.String(20), nullable=False)  # student, teacher, alumni
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        db.UniqueConstraint('skill_id', 'endorser_id', name='unique_endorsement'),
    )


class Experience(db.Model):
    """Work experience or internships"""
    __tablename__ = 'experience'
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('user_profile.id'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(100))
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)  # NULL means currently working
    is_current = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Hobby(db.Model):
    """Hobbies and interests"""
    __tablename__ = 'hobby'
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('user_profile.id'), nullable=False)
    
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # Sports, Arts, Music, Reading, etc.


class Connection(db.Model):
    """Network connections between users"""
    __tablename__ = 'connection'
    id = db.Column(db.Integer, primary_key=True)
    
    requester_id = db.Column(db.String(20), nullable=False)  # Who sent the request
    requester_type = db.Column(db.String(20), nullable=False)
    
    receiver_id = db.Column(db.String(20), nullable=False)  # Who received the request
    receiver_type = db.Column(db.String(20), nullable=False)
    
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    message = db.Column(db.Text)  # Optional connection message
    
    requested_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    responded_at = db.Column(db.DateTime)
    
    __table_args__ = (
        db.UniqueConstraint('requester_id', 'receiver_id', name='unique_connection'),
    )


class Post(db.Model):
    """Social posts/updates"""
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    
    author_id = db.Column(db.String(20), nullable=False)
    author_type = db.Column(db.String(20), nullable=False)
    
    content = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(300))
    
    likes_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    likes = db.relationship('PostLike', backref='post', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('PostComment', backref='post', lazy=True, cascade='all, delete-orphan')


class PostLike(db.Model):
    """Likes on posts"""
    __tablename__ = 'post_like'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    
    user_id = db.Column(db.String(20), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        db.UniqueConstraint('post_id', 'user_id', name='unique_like'),
    )


class PostComment(db.Model):
    """Comments on posts"""
    __tablename__ = 'post_comment'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    
    author_id = db.Column(db.String(20), nullable=False)
    author_type = db.Column(db.String(20), nullable=False)
    
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


# ==================== HELPER FUNCTIONS ====================

def get_user_info(user_id, user_type):
    """Get basic user information"""
    if user_type == 'student':
        user = Student.query.filter_by(student_id=user_id).first()
        return {'name': user.name, 'email': user.email, 'id': user.student_id} if user else None
    elif user_type == 'teacher':
        user = Teacher.query.filter_by(teacher_id=user_id).first()
        return {'name': user.name, 'email': user.email, 'id': user.teacher_id} if user else None
    elif user_type == 'alumni':
        user = Alumni.query.filter_by(alumni_id=user_id).first()
        return {'name': user.name, 'email': user.email, 'id': user.alumni_id} if user else None
    return None


def get_user_profile(user_id, user_type):
    """Get or create user profile"""
    profile = UserProfile.query.filter_by(user_id=user_id, user_type=user_type).first()
    if not profile:
        profile = UserProfile(user_id=user_id, user_type=user_type)
        db.session.add(profile)
        db.session.commit()
    return profile


def get_current_user():
    """Get current logged-in user info"""
    user_type = session.get('user_type')
    if user_type == 'student':
        user = Student.query.get(session.get('student_id'))
        return {'id': user.student_id, 'type': 'student', 'name': user.name, 'email': user.email} if user else None
    elif user_type == 'teacher':
        user = Teacher.query.filter_by(teacher_id=session.get('teacher_id')).first()
        return {'id': user.teacher_id, 'type': 'teacher', 'name': user.name, 'email': user.email} if user else None
    elif user_type == 'alumni':
        user = Alumni.query.filter_by(alumni_id=session.get('alumni_id')).first()
        return {'id': user.alumni_id, 'type': 'alumni', 'name': user.name, 'email': user.email} if user else None
    return None


def are_connected(user1_id, user2_id):
    """Check if two users are connected"""
    connection = Connection.query.filter(
        ((Connection.requester_id == user1_id) & (Connection.receiver_id == user2_id)) |
        ((Connection.requester_id == user2_id) & (Connection.receiver_id == user1_id))
    ).first()
    return connection and connection.status == 'accepted'


# ==================== AUTHENTICATION DECORATOR ====================

def social_login_required(f):
    """Decorator for routes that require any user login (student, teacher, or alumni)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_type' not in session:
            flash('Please login first', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

#======================DATA BASE ENDS HERE=====================
# ====================  ROUTES STARTS ====================

@app.route('/alumni/register', methods=['GET', 'POST'])
def alumni_register():
    if request.method == 'POST':
        name = request.form['name']
        # email = request.form['email']
        stu_id=request.form['stu_id']
        password = request.form['password']
        graduation_year = int(request.form['graduation_year'])
        degree = request.form.get('degree', '')
        major = request.form.get('major', '')
        phone = request.form.get('phone', '')
        
        existing = Alumni.query.filter_by(stu_id=stu_id).first()
        student=Student.query.filter_by(student_id=stu_id).first()
        if existing:
            flash('Alumni already registered', 'error')
            return redirect(url_for('alumni_register'))
        elif not student:
            # Case: The ID does NOT exist in the Student table (Invalid ID)
            flash('Invalid Student ID. Please check your records.', 'error')
            return redirect(url_for('alumni_register'))
        
        new_alumni = Alumni(
            name=name,
            stu_id=stu_id,
            graduation_year=graduation_year,
            degree=degree,
            major=major,
            phone=phone
        )
        new_alumni.set_password(password)
        db.session.add(new_alumni)
        db.session.commit()
        
        new_alumni.alumni_id = f'ALM_{new_alumni.id:03d}'
        db.session.commit()
        
        # Create profile
        get_user_profile(new_alumni.alumni_id, 'alumni')
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('alumni_login'))
    
    return render_template('alumni_register.html')


@app.route('/alumni/login', methods=['GET', 'POST'])
def alumni_login():
    if request.method == 'POST':
        # email = request.form['email']
        stu_id=request.form['stu_id']
        password = request.form['password']
        
        alumni = Alumni.query.filter_by(stu_id=stu_id).first()
        
        if alumni and alumni.check_password(password):
            session['alumni_id'] = alumni.alumni_id
            session['user_type'] = 'alumni'
            flash('Login successful!', 'success')
            return redirect(url_for('social_dashboard'))
        else:
            flash('Invalid  or id or password', 'error')
    
    return render_template('alumni_login.html')


# ==================== SOCIAL DASHBOARD ====================

@app.route('/social/dashboard')
@social_login_required
def social_dashboard():
    """Main social networking dashboard"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    # Get connection stats
    connections_count = Connection.query.filter(
        ((Connection.requester_id == current['id']) | (Connection.receiver_id == current['id'])) &
        (Connection.status == 'accepted')
    ).count()
    
    pending_requests = Connection.query.filter_by(
        receiver_id=current['id'],
        status='pending'
    ).count()
    
    # Get recent posts from connections
    my_connections = Connection.query.filter(
        ((Connection.requester_id == current['id']) | (Connection.receiver_id == current['id'])) &
        (Connection.status == 'accepted')
    ).all()
    
    connection_ids = []
    for conn in my_connections:
        if conn.requester_id == current['id']:
            connection_ids.append(conn.receiver_id)
        else:
            connection_ids.append(conn.requester_id)
    
    # Include own posts
    connection_ids.append(current['id'])
    
    recent_posts = Post.query.filter(Post.author_id.in_(connection_ids)).order_by(Post.created_at.desc()).limit(20).all()
    
    # Add author info to posts
    for post in recent_posts:
        post.author_info = get_user_info(post.author_id, post.author_type)
        post.has_liked = PostLike.query.filter_by(post_id=post.id, user_id=current['id']).first() is not None
    
    stats = {
        'connections': connections_count,
        'pending_requests': pending_requests,
        'achievements': len(profile.achievements),
        'skills': len(profile.skills)
    }
    
    return render_template('social_dashboard.html',
                         current_user=current,
                         profile=profile,
                         stats=stats,
                         posts=recent_posts)


# ==================== PROFILE MANAGEMENT ====================

@app.route('/social/profile')
@social_login_required
def my_profile():
    """View own profile"""
    current = get_current_user()
    return redirect(url_for('view_profile', user_id=current['id'], user_type=current['type']))


@app.route('/social/profile/<user_type>/<user_id>')
@social_login_required
def view_profile(user_type, user_id):
    """View any user's profile"""
    current = get_current_user()
    
    # Get profile owner info
    owner = get_user_info(user_id, user_type)
    if not owner:
        flash('User not found', 'error')
        return redirect(url_for('social_dashboard'))
    
    profile = get_user_profile(user_id, user_type)
    
    # Check if viewing own profile
    is_own_profile = (current['id'] == user_id and current['type'] == user_type)
    
    # Check connection status
    connection_status = None
    if not is_own_profile:
        conn = Connection.query.filter(
            ((Connection.requester_id == current['id']) & (Connection.receiver_id == user_id)) |
            ((Connection.requester_id == user_id) & (Connection.receiver_id == current['id']))
        ).first()
        
        if conn:
            if conn.status == 'accepted':
                connection_status = 'connected'
            elif conn.requester_id == current['id']:
                connection_status = 'pending_sent'
            else:
                connection_status = 'pending_received'
    
    # Get connections count
    connections_count = Connection.query.filter(
        ((Connection.requester_id == user_id) | (Connection.receiver_id == user_id)) &
        (Connection.status == 'accepted')
    ).count()
    
    # Get user's posts
    user_posts = Post.query.filter_by(author_id=user_id, author_type=user_type).order_by(Post.created_at.desc()).limit(10).all()
    for post in user_posts:
        post.author_info = owner
        post.has_liked = PostLike.query.filter_by(post_id=post.id, user_id=current['id']).first() is not None
    
    return render_template('view_profile.html',
                         current_user=current,
                         owner=owner,
                         profile=profile,
                         is_own_profile=is_own_profile,
                         connection_status=connection_status,
                         connections_count=connections_count,
                         posts=user_posts)


@app.route('/social/profile/edit', methods=['GET', 'POST'])
@social_login_required
def edit_profile():
    """Edit own profile"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    if request.method == 'POST':
        profile.bio = request.form.get('bio', '')
        profile.headline = request.form.get('headline', '')
        profile.location = request.form.get('location', '')
        profile.website = request.form.get('website', '')
        profile.linkedin_url = request.form.get('linkedin_url', '')
        profile.github_url = request.form.get('github_url', '')
        
        profile.is_profile_public = 'is_profile_public' in request.form
        profile.show_email = 'show_email' in request.form
        profile.show_phone = 'show_phone' in request.form
        
        # Handle profile picture upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"profile_{current['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'profiles', filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                file.save(filepath)
                profile.profile_picture = filepath
        
        profile.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('my_profile'))
    
    return render_template('edit_profile.html', current_user=current, profile=profile)



#========================social achivement mangement===============
@app.route('/social/achievements/add', methods=['GET', 'POST'])
@social_login_required
def add_achievement():
    """Add new achievement"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description', '')
        category = request.form['category']
        date_achieved = datetime.strptime(request.form['date_achieved'], '%Y-%m-%d').date()
        issuer = request.form.get('issuer', '')
        certificate_url = request.form.get('certificate_url', '')
        
        new_achievement = Achievement(
            profile_id=profile.id,
            title=title,
            description=description,
            category=category,
            date_achieved=date_achieved,
            issuer=issuer,
            certificate_url=certificate_url
        )
        
        db.session.add(new_achievement)
        db.session.commit()
        
        flash('Achievement added successfully!', 'success')
        return redirect(url_for('my_profile'))
    
    return render_template('add_achievement.html', current_user=current)

@app.route('/social/achievements/<int:achievement_id>/edit', methods=['GET', 'POST'])
@social_login_required
def edit_achievement(achievement_id):
    """Edit achievement"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    achievement = Achievement.query.get_or_404(achievement_id)
    
    if achievement.profile_id != profile.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('my_profile'))
    
    if request.method == 'POST':
        achievement.title = request.form['title']
        achievement.description = request.form.get('description', '')
        achievement.category = request.form['category']
        achievement.date_achieved = datetime.strptime(request.form['date_achieved'], '%Y-%m-%d').date()
        achievement.issuer = request.form.get('issuer', '')
        achievement.certificate_url = request.form.get('certificate_url', '')
        
        db.session.commit()
        
        flash('Achievement updated successfully!', 'success')
        return redirect(url_for('my_profile'))
    
    return render_template('edit_achievement.html', current_user=current, achievement=achievement)

@app.route('/social/achievements/<int:achievement_id>/delete', methods=['POST'])
@social_login_required
def delete_achievement(achievement_id):
    """Delete achievement"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    achievement = Achievement.query.get_or_404(achievement_id)
    
    if achievement.profile_id != profile.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('my_profile'))
    
    db.session.delete(achievement)
    db.session.commit()
    
    flash('Achievement deleted', 'success')
    return redirect(url_for('my_profile'))

#========SKILLS ADD ==============
@app.route('/social/skills/add', methods=['GET', 'POST'])
@social_login_required
def add_skill():
    """Add new skill"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    if request.method == 'POST':
        name = request.form['name']
        proficiency = request.form['proficiency']
        category = request.form['category']
        
        # Check if skill already exists for this profile
        existing = Skill.query.filter_by(profile_id=profile.id, name=name).first()
        if existing:
            flash('This skill already exists in your profile', 'warning')
            return redirect(url_for('add_skill'))
        
        new_skill = Skill(
            profile_id=profile.id,
            name=name,
            proficiency=proficiency,
            category=category
        )
        
        db.session.add(new_skill)
        db.session.commit()
        
        flash('Skill added successfully!', 'success')
        return redirect(url_for('my_profile'))
    
    return render_template('add_skill.html', current_user=current)

@app.route('/social/skills/<int:skill_id>/edit', methods=['GET', 'POST'])
@social_login_required
def edit_skill(skill_id):
    """Edit skill"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    skill = Skill.query.get_or_404(skill_id)
    
    if skill.profile_id != profile.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('my_profile'))
    
    if request.method == 'POST':
        skill.name = request.form['name']
        skill.proficiency = request.form['proficiency']
        skill.category = request.form['category']
        
        db.session.commit()
        
        flash('Skill updated successfully!', 'success')
        return redirect(url_for('my_profile'))
    
    return render_template('edit_skill.html', current_user=current, skill=skill)

@app.route('/social/skills/<int:skill_id>/endorse', methods=['POST'])
@social_login_required
def endorse_skill(skill_id):
    """Endorse a skill"""
    current = get_current_user()
    skill = Skill.query.get_or_404(skill_id)
    
    # Check if already endorsed
    existing = SkillEndorsement.query.filter_by(skill_id=skill_id, endorser_id=current['id']).first()
    if existing:
        flash('You have already endorsed this skill', 'warning')
        return redirect(request.referrer or url_for('social_dashboard'))
    
    # Can't endorse own skills
    if skill.profile.user_id == current['id']:
        flash('You cannot endorse your own skills', 'error')
        return redirect(request.referrer or url_for('social_dashboard'))
    
    new_endorsement = SkillEndorsement(
        skill_id=skill_id,
        endorser_id=current['id'],
        endorser_type=current['type']
    )
    
    db.session.add(new_endorsement)
    db.session.commit()
    
    flash('Skill endorsed!', 'success')
    return redirect(request.referrer or url_for('social_dashboard'))

@app.route('/social/skills/<int:skill_id>/delete', methods=['POST'])
@social_login_required
def delete_skill(skill_id):
    """Delete skill"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    skill = Skill.query.get_or_404(skill_id)
    
    if skill.profile_id != profile.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('my_profile'))
    
    db.session.delete(skill)
    db.session.commit()
    
    flash('Skill deleted', 'success')
    return redirect(url_for('my_profile'))

@app.route('/social/skills/<int:skill_id>/unendorse', methods=['POST'])
@social_login_required
def unendorse_skill(skill_id):
    """Remove skill endorsement"""
    current = get_current_user()
    
    endorsement = SkillEndorsement.query.filter_by(
        skill_id=skill_id, 
        endorser_id=current['id']
    ).first()
    
    if endorsement:
        db.session.delete(endorsement)
        db.session.commit()
        flash('Endorsement removed', 'info')
    
    return redirect(request.referrer or url_for('social_dashboard'))


# ==================== EXPERIENCE MANAGEMENT ====================
@app.route('/social/experience/add', methods=['GET', 'POST'])
@social_login_required
def add_experience():
    """Add work experience"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    if request.method == 'POST':
        title = request.form['title']
        company = request.form['company']
        location = request.form.get('location', '')
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        is_current = 'is_current' in request.form
        end_date = None if is_current else datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        description = request.form.get('description', '')
        
        new_experience = Experience(
            profile_id=profile.id,
            title=title,
            company=company,
            location=location,
            start_date=start_date,
            end_date=end_date,
            is_current=is_current,
            description=description
        )
        
        db.session.add(new_experience)
        db.session.commit()
        
        flash('Experience added successfully!', 'success')
        return redirect(url_for('my_profile'))
    
    return render_template('add_experience.html', current_user=current)


@app.route('/social/experience/<int:exp_id>/edit', methods=['GET', 'POST'])
@social_login_required
def edit_experience(exp_id):
    """Edit experience"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    experience = Experience.query.get_or_404(exp_id)
    
    if experience.profile_id != profile.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('my_profile'))
    
    if request.method == 'POST':
        experience.title = request.form['title']
        experience.company = request.form['company']
        experience.location = request.form.get('location', '')
        experience.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        experience.is_current = 'is_current' in request.form
        experience.end_date = None if experience.is_current else datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        experience.description = request.form.get('description', '')
        
        db.session.commit()
        
        flash('Experience updated successfully!', 'success')
        return redirect(url_for('my_profile'))
    
    return render_template('edit_experience.html', current_user=current, experience=experience)


@app.route('/social/experience/<int:exp_id>/delete', methods=['POST'])
@social_login_required
def delete_experience(exp_id):
    """Delete experience"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    experience = Experience.query.get_or_404(exp_id)
    
    if experience.profile_id != profile.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('my_profile'))
    
    db.session.delete(experience)
    db.session.commit()
    
    flash('Experience deleted', 'success')
    return redirect(url_for('my_profile'))

# ==================== HOBBY MANAGEMENT ====================

@app.route('/social/hobbies/add', methods=['GET', 'POST'])
@social_login_required
def add_hobby():
    """Add hobby"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        category = request.form['category']
        
        new_hobby = Hobby(
            profile_id=profile.id,
            name=name,
            description=description,
            category=category
        )
        
        db.session.add(new_hobby)
        db.session.commit()
        
        flash('Hobby added successfully!', 'success')
        return redirect(url_for('my_profile'))
    
    return render_template('add_hobby.html', current_user=current)


@app.route('/social/hobbies/<int:hobby_id>/edit', methods=['GET', 'POST'])
@social_login_required
def edit_hobby(hobby_id):
    """Edit hobby"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    hobby = Hobby.query.get_or_404(hobby_id)
    
    if hobby.profile_id != profile.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('my_profile'))
    
    if request.method == 'POST':
        hobby.name = request.form['name']
        hobby.description = request.form.get('description', '')
        hobby.category = request.form['category']
        
        db.session.commit()
        
        flash('Hobby updated successfully!', 'success')
        return redirect(url_for('my_profile'))
    
    return render_template('edit_hobby.html', current_user=current, hobby=hobby)


@app.route('/social/hobbies/<int:hobby_id>/delete', methods=['POST'])
@social_login_required
def delete_hobby(hobby_id):
    """Delete hobby"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    hobby = Hobby.query.get_or_404(hobby_id)
    
    if hobby.profile_id != profile.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('my_profile'))
    
    db.session.delete(hobby)
    db.session.commit()
    
    flash('Hobby deleted', 'success')
    return redirect(url_for('my_profile'))


# ==================== CONNECTION MANAGEMENT ====================

@app.route('/social/connect/<user_type>/<user_id>', methods=['POST'])
@social_login_required
def send_connection_request(user_type, user_id):
    """Send connection request"""
    current = get_current_user()
    
    # Can't connect to self
    if current['id'] == user_id and current['type'] == user_type:
        flash('You cannot connect with yourself', 'error')
        return redirect(request.referrer or url_for('social_dashboard'))
    
    # Check if connection already exists
    existing = Connection.query.filter(
        ((Connection.requester_id == current['id']) & (Connection.receiver_id == user_id)) |
        ((Connection.requester_id == user_id) & (Connection.receiver_id == current['id']))
    ).first()
    
    if existing:
        flash('Connection request already exists', 'warning')
        return redirect(request.referrer or url_for('social_dashboard'))
    
    message = request.form.get('message', '')
    
    new_connection = Connection(
        requester_id=current['id'],
        requester_type=current['type'],
        receiver_id=user_id,
        receiver_type=user_type,
        message=message
    )
    
    db.session.add(new_connection)
    db.session.commit()
    
    flash('Connection request sent!', 'success')
    return redirect(request.referrer or url_for('social_dashboard'))


@app.route('/social/connections')
@social_login_required
def my_connections():
    """View all connections"""
    current = get_current_user()
    
    # Get accepted connections
    connections = Connection.query.filter(
        ((Connection.requester_id == current['id']) | (Connection.receiver_id == current['id'])) &
        (Connection.status == 'accepted')
    ).all()
    
    connection_list = []
    for conn in connections:
        if conn.requester_id == current['id']:
            other_id = conn.receiver_id
            other_type = conn.receiver_type
        else:
            other_id = conn.requester_id
            other_type = conn.requester_type
        
        user_info = get_user_info(other_id, other_type)
        profile = get_user_profile(other_id, other_type)
        connection_list.append({
            'user': user_info,
            'type': other_type,
            'profile': profile,
            'connected_at': conn.responded_at or conn.requested_at,
            'connection_id': conn.id
        })
    
    # Get pending requests (received)
    pending_requests = Connection.query.filter_by(
        receiver_id=current['id'],
        status='pending'
    ).all()
    
    pending_list = []
    for req in pending_requests:
        user_info = get_user_info(req.requester_id, req.requester_type)
        profile = get_user_profile(req.requester_id, req.requester_type)
        pending_list.append({
            'request': req,
            'user': user_info,
            'type': req.requester_type,
            'profile': profile
        })
    
    # Get sent requests
    sent_requests = Connection.query.filter_by(
        requester_id=current['id'],
        status='pending'
    ).all()
    
    sent_list = []
    for req in sent_requests:
        user_info = get_user_info(req.receiver_id, req.receiver_type)
        sent_list.append({
            'request': req,
            'user': user_info,
            'type': req.receiver_type
        })
    
    return render_template('my_connections.html',
                         current_user=current,
                         connections=connection_list,
                         pending_requests=pending_list,
                         sent_requests=sent_list)


@app.route('/social/connection/<int:connection_id>/accept', methods=['POST'])
@social_login_required
def accept_connection(connection_id):
    """Accept connection request"""
    current = get_current_user()
    connection = Connection.query.get_or_404(connection_id)
    
    if connection.receiver_id != current['id']:
        flash('Unauthorized', 'error')
        return redirect(url_for('my_connections'))
    
    connection.status = 'accepted'
    connection.responded_at = datetime.now(timezone.utc)
    db.session.commit()
    
    flash('Connection accepted!', 'success')
    return redirect(url_for('my_connections'))


@app.route('/social/connection/<int:connection_id>/reject', methods=['POST'])
@social_login_required
def reject_connection(connection_id):
    """Reject connection request"""
    current = get_current_user()
    connection = Connection.query.get_or_404(connection_id)
    
    if connection.receiver_id != current['id']:
        flash('Unauthorized', 'error')
        return redirect(url_for('my_connections'))
    
    connection.status = 'rejected'
    connection.responded_at = datetime.now(timezone.utc)
    db.session.commit()
    
    flash('Connection rejected', 'info')
    return redirect(url_for('my_connections'))


@app.route('/social/connection/<int:connection_id>/cancel', methods=['POST'])
@social_login_required
def cancel_connection_request(connection_id):
    """Cancel sent connection request"""
    current = get_current_user()
    connection = Connection.query.get_or_404(connection_id)
    
    if connection.requester_id != current['id']:
        flash('Unauthorized', 'error')
        return redirect(url_for('my_connections'))
    
    db.session.delete(connection)
    db.session.commit()
    
    flash('Connection request cancelled', 'info')
    return redirect(url_for('my_connections'))


@app.route('/social/connection/<int:connection_id>/remove', methods=['POST'])
@social_login_required
def remove_connection(connection_id):
    """Remove existing connection"""
    current = get_current_user()
    connection = Connection.query.get_or_404(connection_id)
    
    if connection.requester_id != current['id'] and connection.receiver_id != current['id']:
        flash('Unauthorized', 'error')
        return redirect(url_for('my_connections'))
    
    db.session.delete(connection)
    db.session.commit()
    
    flash('Connection removed', 'info')
    return redirect(url_for('my_connections'))

# ==================== SEARCH & DISCOVERY ====================

@app.route('/social/search')
@social_login_required
def search_people():
    """Search for people"""
    current = get_current_user()
    
    query = request.args.get('q', '')
    filter_type = request.args.get('type', 'all')  # all, students, teachers, alumni
    filter_skill = request.args.get('skill', '')
    filter_hobby = request.args.get('hobby', '')
    filter_achievement = request.args.get('achievement', '')
    
    results = []
    
    if query or filter_skill or filter_hobby or filter_achievement:
        # Search students
        if filter_type in ['all', 'students']:
            students = Student.query.filter(
                (Student.name.ilike(f'%{query}%')) | (Student.email.ilike(f'%{query}%'))
            ).all()
            
            for student in students:
                profile = get_user_profile(student.student_id, 'student')
                
                # Apply filters
                if filter_skill:
                    if not any(s.name.lower() == filter_skill.lower() for s in profile.skills):
                        continue
                if filter_hobby:
                    if not any(h.name.lower() == filter_hobby.lower() for h in profile.hobbies):
                        continue
                if filter_achievement:
                    if not any(filter_achievement.lower() in a.title.lower() for a in profile.achievements):
                        continue
                
                results.append({
                    'user': {'name': student.name, 'email': student.email, 'id': student.student_id},
                    'type': 'student',
                    'profile': profile
                })
        
        # Search teachers
        if filter_type in ['all', 'teachers']:
            teachers = Teacher.query.filter(
                (Teacher.name.ilike(f'%{query}%')) | (Teacher.email.ilike(f'%{query}%'))
            ).all()
            
            for teacher in teachers:
                profile = get_user_profile(teacher.teacher_id, 'teacher')
                
                if filter_skill:
                    if not any(s.name.lower() == filter_skill.lower() for s in profile.skills):
                        continue
                if filter_hobby:
                    if not any(h.name.lower() == filter_hobby.lower() for h in profile.hobbies):
                        continue
                if filter_achievement:
                    if not any(filter_achievement.lower() in a.title.lower() for a in profile.achievements):
                        continue
                
                results.append({
                    'user': {'name': teacher.name, 'email': teacher.email, 'id': teacher.teacher_id},
                    'type': 'teacher',
                    'profile': profile
                })
        
        # Search alumni
        if filter_type in ['all', 'alumni']:
            alumni_list = Alumni.query.filter(
                (Alumni.name.ilike(f'%{query}%')) | (Alumni.email.ilike(f'%{query}%'))
            ).all()
            
            for alumni in alumni_list:
                profile = get_user_profile(alumni.alumni_id, 'alumni')
                
                if filter_skill:
                    if not any(s.name.lower() == filter_skill.lower() for s in profile.skills):
                        continue
                if filter_hobby:
                    if not any(h.name.lower() == filter_hobby.lower() for h in profile.hobbies):
                        continue
                if filter_achievement:
                    if not any(filter_achievement.lower() in a.title.lower() for a in profile.achievements):
                        continue
                
                results.append({
                    'user': {'name': alumni.name, 'email': alumni.email, 'id': alumni.alumni_id},
                    'type': 'alumni',
                    'profile': profile
                })
    
    # Add connection status to results
    for result in results:
        result['connection_status'] = None
        if result['user']['id'] != current['id']:
            conn = Connection.query.filter(
                ((Connection.requester_id == current['id']) & (Connection.receiver_id == result['user']['id'])) |
                ((Connection.requester_id == result['user']['id']) & (Connection.receiver_id == current['id']))
            ).first()
            
            if conn:
                if conn.status == 'accepted':
                    result['connection_status'] = 'connected'
                elif conn.requester_id == current['id']:
                    result['connection_status'] = 'pending_sent'
                else:
                    result['connection_status'] = 'pending_received'    
    
    return render_template('search_people.html',
                         current_user=current,
                         results=results,
                         query=query,
                         filter_type=filter_type,
                         filter_skill=filter_skill,
                         filter_hobby=filter_hobby,
                         filter_achievement=filter_achievement)


@app.route('/social/discover')
@social_login_required
def discover():
    """Discover new people to connect with"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    # Getting users with similar skills
    my_skills = [s.name.lower() for s in profile.skills]
    
    suggestions = []
    
    # Getring all profiles with skills
    all_profiles = UserProfile.query.filter(
        UserProfile.user_id != current['id']
    ).limit(50).all()
    
    for p in all_profiles:
        # Skip if already connected
        if are_connected(current['id'], p.user_id):
            continue
        
        # Check for pending connection
        conn = Connection.query.filter(
            ((Connection.requester_id == current['id']) & (Connection.receiver_id == p.user_id)) |
            ((Connection.requester_id == p.user_id) & (Connection.receiver_id == current['id']))
        ).first()
        
        if conn:
            continue
        
        # Calculate match score
        their_skills = [s.name.lower() for s in p.skills]
        common_skills = set(my_skills) & set(their_skills)
        
        if len(common_skills) > 0 or len(suggestions) < 20:
            user_info = get_user_info(p.user_id, p.user_type)
            if user_info:
                suggestions.append({
                    'user': user_info,
                    'type': p.user_type,
                    'profile': p,
                    'common_skills': list(common_skills),
                    'match_score': len(common_skills)
                })
    
    # Sort by match score
    suggestions.sort(key=lambda x: x['match_score'], reverse=True)
    
    return render_template('discover.html',
                         current_user=current,
                         suggestions=suggestions[:20])




# ==================== POST MANAGEMENT ====================

@app.route('/social/post/create', methods=['GET', 'POST'])
@social_login_required
def create_post():
    """Create a new post"""
    current = get_current_user()
    
    if request.method == 'POST':
        content = request.form['content']
        
        # Handle image upload
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"post_{current['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'posts', filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                file.save(filepath)
                image_path = filepath
        
        new_post = Post(
            author_id=current['id'],
            author_type=current['type'],
            content=content,
            image_path=image_path
        )
        
        db.session.add(new_post)
        db.session.commit()
        
        flash('Post created successfully!', 'success')
        return redirect(url_for('social_dashboard'))
    
    return render_template('create_post.html', current_user=current)


@app.route('/social/post/<int:post_id>')
@social_login_required
def view_post(post_id):
    """View single post with comments"""
    current = get_current_user()
    post = Post.query.get_or_404(post_id)
    
    # Get author info
    post.author_info = get_user_info(post.author_id, post.author_type)
    post.has_liked = PostLike.query.filter_by(post_id=post.id, user_id=current['id']).first() is not None
    
    # Get comments with author info
    comments = PostComment.query.filter_by(post_id=post_id).order_by(PostComment.created_at.desc()).all()
    for comment in comments:
        comment.author_info = get_user_info(comment.author_id, comment.author_type)
    
    return render_template('view_post.html',
                         current_user=current,
                         post=post,
                         comments=comments)


@app.route('/social/post/<int:post_id>/edit', methods=['GET', 'POST'])
@social_login_required
def edit_post(post_id):
    """Edit a post"""
    current = get_current_user()
    post = Post.query.get_or_404(post_id)
    
    # Check ownership
    if post.author_id != current['id'] or post.author_type != current['type']:
        flash('Unauthorized', 'error')
        return redirect(url_for('social_dashboard'))
    
    if request.method == 'POST':
        post.content = request.form['content']
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"post_{current['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'posts', filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                file.save(filepath)
                
                # Delete old image if exists
                if post.image_path and os.path.exists(post.image_path):
                    os.remove(post.image_path)
                
                post.image_path = filepath
        
        post.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        flash('Post updated!', 'success')
        return redirect(url_for('view_post', post_id=post_id))
    
    return render_template('edit_post.html', current_user=current, post=post)


@app.route('/social/post/<int:post_id>/delete', methods=['POST'])
@social_login_required
def delete_post(post_id):
    """Delete a post"""
    current = get_current_user()
    post = Post.query.get_or_404(post_id)
    
    # Check ownership
    if post.author_id != current['id'] or post.author_type != current['type']:
        flash('Unauthorized', 'error')
        return redirect(url_for('social_dashboard'))
    
    # Delete image if exists
    if post.image_path and os.path.exists(post.image_path):
        os.remove(post.image_path)
    
    db.session.delete(post)
    db.session.commit()
    
    flash('Post deleted', 'info')
    return redirect(url_for('social_dashboard'))


@app.route('/social/post/<int:post_id>/like', methods=['POST'])
@social_login_required
def like_post(post_id):
    """Like/unlike a post"""
    current = get_current_user()
    post = Post.query.get_or_404(post_id)
    
    # Check if already liked
    existing_like = PostLike.query.filter_by(post_id=post_id, user_id=current['id']).first()
    
    if existing_like:
        # Unlike
        db.session.delete(existing_like)
        post.likes_count = max(0, post.likes_count - 1)
        action = 'unliked'
    else:
        # Like
        new_like = PostLike(
            post_id=post_id,
            user_id=current['id'],
            user_type=current['type']
        )
        db.session.add(new_like)
        post.likes_count += 1
        action = 'liked'
    
    db.session.commit()
    
    # Return JSON for AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'action': action,
            'likes_count': post.likes_count
        })
    
    return redirect(request.referrer or url_for('social_dashboard'))


@app.route('/social/post/<int:post_id>/comment', methods=['POST'])
@social_login_required
def comment_post(post_id):
    """Add a comment to a post"""
    current = get_current_user()
    post = Post.query.get_or_404(post_id)
    
    content = request.form['content']
    
    if not content.strip():
        flash('Comment cannot be empty', 'error')
        return redirect(request.referrer or url_for('view_post', post_id=post_id))
    
    new_comment = PostComment(
        post_id=post_id,
        author_id=current['id'],
        author_type=current['type'],
        content=content
    )
    
    db.session.add(new_comment)
    post.comments_count += 1
    db.session.commit()
    
    flash('Comment added!', 'success')
    return redirect(request.referrer or url_for('view_post', post_id=post_id))


@app.route('/social/comment/<int:comment_id>/delete', methods=['POST'])
@social_login_required
def delete_comment(comment_id):
    """Delete a comment"""
    current = get_current_user()
    comment = PostComment.query.get_or_404(comment_id)
    
    # Check ownership
    if comment.author_id != current['id'] or comment.author_type != current['type']:
        flash('Unauthorized', 'error')
        return redirect(request.referrer or url_for('social_dashboard'))
    
    post = comment.post
    post.comments_count = max(0, post.comments_count - 1)
    
    db.session.delete(comment)
    db.session.commit()
    
    flash('Comment deleted', 'info')
    return redirect(request.referrer or url_for('view_post', post_id=post.id))


# ==================== DISCOVER & SUGGESTIONS ====================



# ==================== ALUMNI SPECIFIC ====================

@app.route('/social/alumni')
@social_login_required
def alumni_directory():
    """Browse alumni directory"""
    current = get_current_user()
    
    # Filters
    graduation_year = request.args.get('year', type=int)
    company = request.args.get('company', '')
    
    query = Alumni.query
    
    if graduation_year:
        query = query.filter_by(graduation_year=graduation_year)
    if company:
        query = query.filter(Alumni.current_company.ilike(f'%{company}%'))
    
    alumni_list = query.order_by(Alumni.graduation_year.desc()).all()
    
    # Get unique graduation years for filter
    years = db.session.query(Alumni.graduation_year).distinct().order_by(Alumni.graduation_year.desc()).all()
    years = [y[0] for y in years]
    
    # Add profile and connection info
    alumni_data = []
    for alumni in alumni_list:
        profile = get_user_profile(alumni.alumni_id, 'alumni')
        
        # Check connection status
        connection_status = None
        if alumni.alumni_id != current['id']:
            conn = Connection.query.filter(
                ((Connection.requester_id == current['id']) & (Connection.receiver_id == alumni.alumni_id)) |
                ((Connection.requester_id == alumni.alumni_id) & (Connection.receiver_id == current['id']))
            ).first()
            
            if conn:
                if conn.status == 'accepted':
                    connection_status = 'connected'
                elif conn.requester_id == current['id']:
                    connection_status = 'pending_sent'
                else:
                    connection_status = 'pending_received'
        
        alumni_data.append({
            'alumni': alumni,
            'profile': profile,
            'connection_status': connection_status
        })
    
    return render_template('alumni_directory.html',
                         current_user=current,
                         alumni_list=alumni_data,
                         years=years,
                         selected_year=graduation_year,
                         company_filter=company)


# ==================== NOTIFICATIONS ====================

@app.route('/social/notifications')
@social_login_required
def social_notifications():
    """View social notifications"""
    current = get_current_user()
    
    # Get connection requests
    connection_requests = Connection.query.filter_by(
        receiver_id=current['id'],
        status='pending'
    ).order_by(Connection.requested_at.desc()).all()
    
    notifications = []
    
    for req in connection_requests:
        user_info = get_user_info(req.requester_id, req.requester_type)
        notifications.append({
            'type': 'connection_request',
            'user': user_info,
            'user_type': req.requester_type,
            'connection': req,
            'time': req.requested_at
        })
    
    # Get recent endorsements
    my_profile = get_user_profile(current['id'], current['type'])
    recent_endorsements = []
    
    for skill in my_profile.skills:
        for endorsement in skill.endorsements:
            endorser_info = get_user_info(endorsement.endorser_id, endorsement.endorser_type)
            recent_endorsements.append({
                'type': 'skill_endorsement',
                'user': endorser_info,
                'skill': skill.name,
                'time': endorsement.created_at
            })
    
    # Sort by time and limit
    recent_endorsements.sort(key=lambda x: x['time'], reverse=True)
    notifications.extend(recent_endorsements[:10])
    
    # Sort all notifications by time
    notifications.sort(key=lambda x: x['time'], reverse=True)
    
    return render_template('social_notifications.html',
                         current_user=current,
                         notifications=notifications)


# ==================== API ENDPOINTS ====================

@app.route('/api/social/check_connection/<user_type>/<user_id>')
@social_login_required
def api_check_connection(user_type, user_id):
    """API to check connection status"""
    current = get_current_user()
    
    conn = Connection.query.filter(
        ((Connection.requester_id == current['id']) & (Connection.receiver_id == user_id)) |
        ((Connection.requester_id == user_id) & (Connection.receiver_id == current['id']))
    ).first()
    
    if not conn:
        return jsonify({'status': 'not_connected'})
    
    if conn.status == 'accepted':
        return jsonify({'status': 'connected'})
    elif conn.requester_id == current['id']:
        return jsonify({'status': 'pending_sent'})
    else:
        return jsonify({'status': 'pending_received', 'connection_id': conn.id})


@app.route('/api/social/suggest_skills')
@social_login_required
def api_suggest_skills():
    """API to get skill suggestions"""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify([])
    
    # Get unique skill names that match
    skills = db.session.query(Skill.name).filter(
        Skill.name.ilike(f'%{query}%')
    ).distinct().limit(10).all()
    
    return jsonify([s[0] for s in skills])


@app.route('/api/social/suggest_hobbies')
@social_login_required
def api_suggest_hobbies():
    """API to get hobby suggestions"""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify([])
    
    hobbies = db.session.query(Hobby.name).filter(
        Hobby.name.ilike(f'%{query}%')
    ).distinct().limit(10).all()
    
    return jsonify([h[0] for h in hobbies])


@app.route('/api/social/stats')
@social_login_required
def api_social_stats():
    """Get user's social stats"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    connections_count = Connection.query.filter(
        ((Connection.requester_id == current['id']) | (Connection.receiver_id == current['id'])) &
        (Connection.status == 'accepted')
    ).count()
    
    posts_count = Post.query.filter_by(author_id=current['id'], author_type=current['type']).count()
    
    # Total endorsements received
    total_endorsements = 0
    for skill in profile.skills:
        total_endorsements += len(skill.endorsements)
    
    return jsonify({
        'connections': connections_count,
        'achievements': len(profile.achievements),
        'skills': len(profile.skills),
        'experiences': len(profile.experiences),
        'hobbies': len(profile.hobbies),
        'posts': posts_count,
        'endorsements': total_endorsements
    })


# ==================== ADMIN - ALUMNI MANAGEMENT ====================

@app.route('/admin/alumni', methods=['GET'])
@admin_required
def list_alumni():
    """List all alumni"""
    alumni_list = Alumni.query.order_by(Alumni.graduation_year.desc()).all()
    return render_template('list_alumni.html', alumni_list=alumni_list)


@app.route('/admin/add_alumni', methods=['GET', 'POST'])
@admin_required
def add_alumni():
    """Add new alumni (admin only)"""
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        graduation_year = int(request.form['graduation_year'])
        degree = request.form.get('degree', '')
        major = request.form.get('major', '')
        phone = request.form.get('phone', '')
        
        existing = Alumni.query.filter_by(email=email).first()
        if existing:
            flash('Email already registered', 'error')
            return redirect(url_for('add_alumni'))
        
        new_alumni = Alumni(
            name=name,
            email=email,
            graduation_year=graduation_year,
            degree=degree,
            major=major,
            phone=phone
        )
        new_alumni.set_password(password)
        db.session.add(new_alumni)
        db.session.commit()
        
        new_alumni.alumni_id = f'ALM_{new_alumni.id:03d}'
        db.session.commit()
        
        # Create profile
        get_user_profile(new_alumni.alumni_id, 'alumni')
        
        flash('Alumni added successfully!', 'success')
        return redirect(url_for('list_alumni'))
    
    return render_template('add_alumni.html')


# Logout function for the social connect app
@app.route('/logout_social')
def logout_social():
    user_type = session.get('user_type')
    session.clear()
    flash('You have been logged out', 'info')
    
    if user_type == 'admin':
        return redirect(url_for('admin_login'))
    elif user_type == 'teacher':
        return redirect(url_for('teacher_login'))
    elif user_type == 'alumni':
        return redirect(url_for('home'))
    else:
        return redirect(url_for('student_login'))

'''====================SOCIAL CONNECT ENDS========================='''

# ==================== LOGIN ROUTES ====================
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and admin.check_password(password):
            session['admin_id'] = admin.id
            session['user_type'] = 'admin'
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('admin_login.html')



@app.route('/teacher/login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        teach = Teacher.query.filter_by(email=email).first()
        
        if teach and teach.check_password(password) and teach.status == 'Active':
            session['teacher_id'] = teach.teacher_id
            session['user_type'] = 'teacher'
            flash('Login successful!', 'success')
            return redirect(url_for('teacher_dashboard'))
        else:
            flash('Invalid email or password or teacher is inactive', 'error')
    
    return render_template('teacher_login.html')


@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        stud = Student.query.filter_by(email=email).first()
        
        if stud and stud.check_password(password):
            session['student_id'] = stud.id
            session['user_type'] = 'student'
            flash('Login successful!', 'success')
            return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('student_login.html')


@app.route('/logout')
def logout():
    user_type = session.get('user_type')
    session.clear()
    flash('You have been logged out', 'info')
    
    if user_type == 'admin':
        return redirect(url_for('admin_login'))
    elif user_type == 'teacher':
        return redirect(url_for('teacher_login'))
    else:
        return redirect(url_for('student_login'))


# ==================== ADMIN DASHBOARD ====================
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    stats = {
        'total_students': Student.query.count(),
        'total_teachers': Teacher.query.count(),
        'total_classes': Classes.query.count(),
        'total_subjects': Subject.query.count(),
        'active_teachers': Teacher.query.filter_by(status='Active').count()
    }
    return render_template('admin_dashboard.html', stats=stats)


# ==================== GRADE MANAGEMENT ====================
@app.route('/admin/grades', methods=['GET'])
@admin_required
def list_grades():
    grades = Grade.query.order_by(Grade.level).all()
    return render_template('list_grades.html', grades=grades)


@app.route('/admin/add_grade', methods=['GET', 'POST'])
@admin_required
def add_grade():
    if request.method == 'POST':
        name = request.form['name']
        level = int(request.form['level'])
        
        new_grade = Grade(name=name, level=level)
        db.session.add(new_grade)
        db.session.flush()
        
        new_grade.grade_id = f'GRD_{new_grade.id:03d}'
        db.session.commit()
        
        flash('Grade added successfully!', 'success')
        return redirect(url_for('list_grades'))
    
    return render_template('add_grade.html')


# ==================== SUBJECT MANAGEMENT ====================
@app.route('/admin/subjects', methods=['GET'])
@admin_required
def list_subjects():
    subjects = Subject.query.all()
    return render_template('list_subjects.html', subjects=subjects)


@app.route('/admin/add_subject', methods=['GET', 'POST'])
@admin_required
def add_subject():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        
        new_subject = Subject(name=name, description=description)
        db.session.add(new_subject)
        db.session.flush()
        
        new_subject.subject_id = f'SUB_{new_subject.id:03d}'
        db.session.commit()
        
        flash('Subject added successfully!', 'success')
        return redirect(url_for('list_subjects'))
    
    return render_template('add_subject.html')


# ==================== CLASS MANAGEMENT ====================
@app.route('/admin/classes', methods=['GET'])
@admin_required
def list_classes():
    classes_list = Classes.query.all()
    return render_template('list_classes.html', classes=classes_list)


@app.route('/admin/add_class', methods=['GET', 'POST'])
@admin_required
def add_class():
    grades = Grade.query.all()
    teachers = Teacher.query.filter_by(status='Active').all()
    
    if request.method == 'POST':
        name = request.form['name']
        section = request.form['section']
        grade_id = request.form['grade_id']
        head = request.form.get('head')
        
        new_class = Classes(
            name=name,
            section=section,
            grade_id=grade_id,
            head=head if head else None
        )
        
        db.session.add(new_class)
        db.session.flush()
        
        new_class.class_id = f'CLS_{new_class.id:03d}'
        db.session.commit()
        
        flash('Class added successfully!', 'success')
        return redirect(url_for('list_classes'))
    
    return render_template('add_class.html', grades=grades, teachers=teachers)


# ==================== TEACHER MANAGEMENT ====================
@app.route('/admin/teachers', methods=['GET'])
@admin_required
def list_teachers():
    teachers = Teacher.query.all()
    return render_template('list_teachers.html', teachers=teachers)


@app.route('/admin/add_teacher', methods=['GET', 'POST'])
@admin_required
def add_teacher():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form.get('phone', '')
        
        existing = Teacher.query.filter_by(email=email).first()
        if existing:
            flash('Email already registered', 'error')
            return redirect(url_for('add_teacher'))
        
        new_teacher = Teacher(name=name, email=email, phone=phone)
        new_teacher.set_password(password)
        db.session.add(new_teacher)
        db.session.commit()
        
        new_teacher.teacher_id = f'TCH_{new_teacher.id:03d}'
        db.session.commit()
        
        flash('Teacher added successfully!', 'success')
        return redirect(url_for('list_teachers'))
    
    return render_template('add_teacher.html')


# ==================== STUDENT MANAGEMENT ====================
@app.route('/admin/students', methods=['GET'])
@admin_required
def list_students():
    students = Student.query.all()
    classes = Classes.query.all()
    return render_template('list_students.html', students=students, classes=classes)


@app.route('/admin/add_student', methods=['GET', 'POST'])
@admin_required
def add_student():
    classes = Classes.query.all()
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        age = int(request.form['age'])
        gender = request.form['gender']
        contact_info = request.form['contact_info']
        parent_name = request.form['parent_name']
        parent_phone = request.form.get('parent_phone', '')
        class_id = request.form.get('class_id')
        
        existing = Student.query.filter_by(email=email).first()
        if existing:
            flash('Email already registered', 'error')
            return redirect(url_for('add_student'))
        
        new_student = Student(
            name=name,
            email=email,
            age=age,
            gender=gender,
            contact_info=contact_info,
            parent_name=parent_name,
            parent_phone=parent_phone,
            class_id=class_id if class_id else None
        )
        new_student.set_password(password)
        db.session.add(new_student)
        db.session.commit()
        
        admission_year = new_student.date_join.year
        count_in_year = Student.query.filter(
            extract('year', Student.date_join) == admission_year
        ).count()
        serial_no = f"{count_in_year:03d}"
        new_student.student_id = f"STU{admission_year}_{serial_no}"
        db.session.commit()
        
        flash('Student added successfully!', 'success')
        return redirect(url_for('list_students'))
    
    return render_template('add_student.html', classes=classes)


# ==================== CLASS-SUBJECT ASSIGNMENT ====================
@app.route('/admin/assign_subject', methods=['GET', 'POST'])
@admin_required
def assign_subject_to_class():
    classes_list = Classes.query.all()
    subjects = Subject.query.all()
    teachers = Teacher.query.filter_by(status='Active').all()
    
    if request.method == 'POST':
        class_id = request.form['class_id']
        subject_id = request.form['subject_id']
        teacher_id = request.form['teacher_id']
        
        existing = ClassSubject.query.filter_by(
            class_id=class_id,
            subject_id=subject_id
        ).first()
        
        if existing:
            flash('This subject is already assigned to this class!', 'error')
            return redirect(url_for('assign_subject_to_class'))
        
        new_assignment = ClassSubject(
            class_id=class_id,
            subject_id=subject_id,
            teacher_id=teacher_id
        )
        db.session.add(new_assignment)
        db.session.commit()
        
        flash('Subject assigned successfully!', 'success')
        return redirect(url_for('view_class_subjects'))
    
    return render_template('assign_subject.html',
                         classes=classes_list,
                         subjects=subjects,
                         teachers=teachers)


@app.route('/admin/class_subjects', methods=['GET'])
@admin_required
def view_class_subjects():
    class_subjects = ClassSubject.query.all()
    return render_template('view_class_subjects.html', class_subjects=class_subjects)


@app.route('/admin/delete_class_subject/<int:id>', methods=['POST'])
@admin_required
def delete_class_subject(id):
    class_subject = ClassSubject.query.get_or_404(id)
    db.session.delete(class_subject)
    db.session.commit()
    flash('Subject removed from class!', 'success')
    return redirect(url_for('view_class_subjects'))


# Phase 2

from werkzeug.utils import secure_filename
import os

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'zip', 'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ==================== TEACHER DASHBOARD ====================
@app.route('/teacher/dashboard')
@teacher_required
def teacher_dashboard():
    teacher_id = session.get('teacher_id')
    teach = Teacher.query.filter_by(teacher_id=teacher_id).first()
    
    # Get teacher's classes and subjects
    my_classes = ClassSubject.query.filter_by(teacher_id=teacher_id).all()
    
    # Statistics
    total_classes = len(set([cs.class_id for cs in my_classes]))
    total_students = 0
    for cs in my_classes:
        total_students += Student.query.filter_by(class_id=cs.class_id).count()
    
    stats = {
        'total_classes': total_classes,
        'total_students': total_students,
        'total_subjects': len(my_classes),
        'pending_submissions': 0  # Calculate later
    }
    
    return render_template('teacher_dashboard.html', teacher=teach, stats=stats, my_classes=my_classes)


@app.route('/teacher/my_classes')
@teacher_required
def teacher_my_classes():
    teacher_id = session.get('teacher_id')
    my_classes = ClassSubject.query.filter_by(teacher_id=teacher_id).all()
    return render_template('teacher_my_classes.html', my_classes=my_classes)


# ==================== ATTENDANCE MANAGEMENT ====================
@app.route('/teacher/attendance', methods=['GET'])
@teacher_required
def attendance_home():
    """Select class and subject for attendance"""
    teacher_id = session.get('teacher_id')
    my_classes = ClassSubject.query.filter_by(teacher_id=teacher_id).all()
    return render_template('teacher_attendance_select.html', my_classes=my_classes)


@app.route('/teacher/mark_attendance/<int:class_subject_id>', methods=['GET', 'POST'])
@teacher_required
def mark_attendance(class_subject_id):
    """Mark attendance for a specific class-subject"""
    teacher_id = session.get('teacher_id')
    
    class_subject = ClassSubject.query.get_or_404(class_subject_id)
    
    # Verify this teacher teaches this class-subject
    if class_subject.teacher_id != teacher_id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    # Get all students in this class
    students = Student.query.filter_by(class_id=class_subject.class_id).all()
    
    if request.method == 'POST':
        attendance_date = request.form.get('date', date.today())
        if isinstance(attendance_date, str):
            attendance_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()
        
        for student in students:
            status = request.form.get(f'status_{student.student_id}')
            remarks = request.form.get(f'remarks_{student.student_id}', '')
            
            if status:
                # Check if attendance already exists
                existing = Attendance.query.filter_by(
                    student_id=student.student_id,
                    date=attendance_date,
                    class_subject_id=class_subject_id
                ).first()
                
                if existing:
                    # Update existing
                    existing.status = status
                    existing.remarks = remarks
                else:
                    # Create new
                    new_attendance = Attendance(
                        student_id=student.student_id,
                        class_id=class_subject.class_id,
                        class_subject_id=class_subject_id,
                        teacher_id=teacher_id,
                        date=attendance_date,
                        status=status,
                        remarks=remarks
                    )
                    db.session.add(new_attendance)
        
        db.session.commit()
        flash('Attendance marked successfully!', 'success')
        return redirect(url_for('attendance_home'))
    
    # Get today's attendance if exists
    today_attendance = {}
    for student in students:
        att = Attendance.query.filter_by(
            student_id=student.student_id,
            date=date.today(),
            class_subject_id=class_subject_id
        ).first()
        if att:
            today_attendance[student.student_id] = att
    
    return render_template('mark_attendance.html',
                         class_subject=class_subject,
                         students=students,
                         today_attendance=today_attendance)


@app.route('/teacher/attendance_report', methods=['GET', 'POST'])
@teacher_required
def attendance_report():
    """View attendance reports"""
    teacher_id = session.get('teacher_id')
    my_classes = ClassSubject.query.filter_by(teacher_id=teacher_id).all()
    
    attendance_data = []
    
    if request.method == 'POST':
        class_subject_id = request.form.get('class_subject_id')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        query = Attendance.query.filter_by(class_subject_id=class_subject_id)
        
        if start_date:
            query = query.filter(Attendance.date >= start_date)
        if end_date:
            query = query.filter(Attendance.date <= end_date)
        
        attendance_data = query.all()
    
    return render_template('attendance_report.html',
                         my_classes=my_classes,
                         attendance_data=attendance_data)


# ==================== MARKS MANAGEMENT ====================
@app.route('/teacher/marks', methods=['GET'])
@teacher_required
def marks_home():
    """Select class and subject for marks entry"""
    teacher_id = session.get('teacher_id')
    my_classes = ClassSubject.query.filter_by(teacher_id=teacher_id).all()
    return render_template('teacher_marks_select.html', my_classes=my_classes)


@app.route('/teacher/add_marks/<int:class_subject_id>', methods=['GET', 'POST'])
@teacher_required
def add_marks(class_subject_id):
    """Add marks for students"""
    teacher_id = session.get('teacher_id')
    
    class_subject = ClassSubject.query.get_or_404(class_subject_id)
    
    if class_subject.teacher_id != teacher_id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    students = Student.query.filter_by(class_id=class_subject.class_id).all()
    
    if request.method == 'POST':
        exam_type = request.form['exam_type']
        total_marks = float(request.form['total_marks'])
        exam_date = request.form.get('date', date.today())
        
        if isinstance(exam_date, str):
            exam_date = datetime.strptime(exam_date, '%Y-%m-%d').date()
        
        for student in students:
            marks_obtained = request.form.get(f'marks_{student.student_id}')
            remarks = request.form.get(f'remarks_{student.student_id}', '')
            
            if marks_obtained:
                marks_obtained = float(marks_obtained)
                
                new_marks = Marks(
                    student_id=student.student_id,
                    class_subject_id=class_subject_id,
                    teacher_id=teacher_id,
                    exam_type=exam_type,
                    marks_obtained=marks_obtained,
                    total_marks=total_marks,
                    date=exam_date,
                    remarks=remarks
                )
                db.session.add(new_marks)
        
        db.session.commit()
        flash('Marks added successfully!', 'success')
        return redirect(url_for('marks_home'))
    
    return render_template('add_marks.html',
                         class_subject=class_subject,
                         students=students)


@app.route('/teacher/view_marks/<int:class_subject_id>', methods=['GET'])
@teacher_required
def view_marks(class_subject_id):
    """View marks for a class-subject"""
    teacher_id = session.get('teacher_id')
    
    class_subject = ClassSubject.query.get_or_404(class_subject_id)
    
    if class_subject.teacher_id != teacher_id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    marks_data = Marks.query.filter_by(class_subject_id=class_subject_id).all()
    
    return render_template('view_marks.html',
                         class_subject=class_subject,
                         marks_data=marks_data)


# ==================== ASSIGNMENT MANAGEMENT ====================
@app.route('/teacher/assignments', methods=['GET'])
@teacher_required
def teacher_assignments():
    """View all assignments created by teacher"""
    teacher_id = session.get('teacher_id')
    assignments = Assignment.query.filter_by(teacher_id=teacher_id).order_by(Assignment.created_at.desc()).all()
    return render_template('teacher_assignments.html', assignments=assignments)


@app.route('/teacher/create_assignment', methods=['GET', 'POST'])
@teacher_required
def create_assignment():
    """Create new assignment"""
    teacher_id = session.get('teacher_id')
    my_classes = ClassSubject.query.filter_by(teacher_id=teacher_id).all()
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d').date()
        total_marks = float(request.form['total_marks'])
        class_subject_id = int(request.form['class_subject_id'])
        
        class_subject = ClassSubject.query.get(class_subject_id)
        
        # Handle file upload
        attachment_path = None
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'assignments', filename)
                file.save(filepath)
                attachment_path = filepath
        
        new_assignment = Assignment(
            title=title,
            description=description,
            due_date=due_date,
            total_marks=total_marks,
            teacher_id=teacher_id,
            class_id=class_subject.class_id,
            class_subject_id=class_subject_id,
            attachment_path=attachment_path
        )
        
        db.session.add(new_assignment)
        db.session.commit()
        
        flash('Assignment created successfully!', 'success')
        return redirect(url_for('teacher_assignments'))
    
    return render_template('create_assignment.html', my_classes=my_classes)


@app.route('/teacher/assignment/<int:assignment_id>/submissions', methods=['GET'])
@teacher_required
def view_submissions(assignment_id):
    """View all submissions for an assignment"""
    teacher_id = session.get('teacher_id')
    assignment = Assignment.query.get_or_404(assignment_id)
    
    if assignment.teacher_id != teacher_id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    submissions = Submission.query.filter_by(assignment_id=assignment_id).all()
    
    # Get students who haven't submitted
    all_students = Student.query.filter_by(class_id=assignment.class_id).all()
    submitted_ids = [s.student_id for s in submissions]
    pending_students = [s for s in all_students if s.student_id not in submitted_ids]
    
    return render_template('view_submissions.html',
                         assignment=assignment,
                         submissions=submissions,
                         pending_students=pending_students)


@app.route('/teacher/grade_submission/<int:submission_id>', methods=['GET', 'POST'])
@teacher_required
def grade_submission(submission_id):
    """Grade a student's submission"""
    teacher_id = session.get('teacher_id')
    submission = Submission.query.get_or_404(submission_id)
    
    if submission.assignment.teacher_id != teacher_id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    if request.method == 'POST':
        marks_obtained = float(request.form['marks_obtained'])
        feedback = request.form.get('feedback', '')
        
        submission.marks_obtained = marks_obtained
        submission.feedback = feedback
        submission.status = 'Graded'
        submission.graded_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        flash('Submission graded successfully!', 'success')
        return redirect(url_for('view_submissions', assignment_id=submission.assignment_id))
    
    return render_template('grade_submission.html', submission=submission)


# ==================== DIARY MANAGEMENT ====================
@app.route('/teacher/diary', methods=['GET'])
@teacher_required
def teacher_diary():
    """View all diary entries"""
    teacher_id = session.get('teacher_id')
    diaries = Diary.query.filter_by(teacher_id=teacher_id).order_by(Diary.date.desc()).all()
    return render_template('teacher_diary.html', diaries=diaries)


@app.route('/teacher/create_diary', methods=['GET', 'POST'])
@teacher_required
def create_diary():
    """Create daily diary entry"""
    teacher_id = session.get('teacher_id')
    my_classes = ClassSubject.query.filter_by(teacher_id=teacher_id).all()
    
    if request.method == 'POST':
        diary_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        notes = request.form['notes']
        homework = request.form.get('homework', '')
        instructions = request.form.get('instructions', '')
        class_subject_id = int(request.form['class_subject_id'])
        
        class_subject = ClassSubject.query.get(class_subject_id)
        
        # Check if diary already exists for this date and class-subject
        existing = Diary.query.filter_by(
            teacher_id=teacher_id,
            class_id=class_subject.class_id,
            class_subject_id=class_subject_id,
            date=diary_date
        ).first()
        
        if existing:
            # Update existing
            existing.notes = notes
            existing.homework = homework
            existing.instructions = instructions
        else:
            # Create new
            new_diary = Diary(
                teacher_id=teacher_id,
                class_id=class_subject.class_id,
                class_subject_id=class_subject_id,
                date=diary_date,
                notes=notes,
                homework=homework,
                instructions=instructions
            )
            db.session.add(new_diary)
        
        db.session.commit()
        flash('Diary entry saved successfully!', 'success')
        return redirect(url_for('teacher_diary'))
    
    return render_template('create_diary.html', my_classes=my_classes)


# ==================== NOTIFICATION MANAGEMENT ====================
@app.route('/teacher/notifications', methods=['GET'])
@teacher_required
def teacher_notifications():
    """View all sent notifications"""
    teacher_id = session.get('teacher_id')
    notifications = Notification.query.filter_by(teacher_id=teacher_id).order_by(Notification.date.desc()).all()
    return render_template('teacher_notifications.html', notifications=notifications)


@app.route('/teacher/send_notification', methods=['GET', 'POST'])
@teacher_required
def send_notification():
    """Send notification to a class"""
    teacher_id = session.get('teacher_id')
    
    # Get unique classes this teacher teaches
    class_subjects = ClassSubject.query.filter_by(teacher_id=teacher_id).all()
    unique_classes = {}
    for cs in class_subjects:
        if cs.class_id not in unique_classes:
            unique_classes[cs.class_id] = cs.class_obj
    
    if request.method == 'POST':
        title = request.form['title']
        message = request.form['message']
        class_id = request.form['class_id']
        is_urgent = 'is_urgent' in request.form
        
        new_notification = Notification(
            teacher_id=teacher_id,
            class_id=class_id,
            title=title,
            message=message,
            is_urgent=is_urgent
        )
        
        db.session.add(new_notification)
        db.session.commit()
        
        flash('Notification sent successfully!', 'success')
        return redirect(url_for('teacher_notifications'))
    
    return render_template('send_notification.html', classes=unique_classes.values())


# ==================== HELPER ROUTES ====================
@app.route('/api/teacher/class/<class_id>/students', methods=['GET'])
@teacher_required
def get_class_students(class_id):
    """API endpoint to get students in a class (for AJAX)"""
    students = Student.query.filter_by(class_id=class_id).all()
    return jsonify([{
        'student_id': s.student_id,
        'name': s.name,
        'email': s.email
    } for s in students])

# ADD THESE ROUTES TO YOUR app.py (after Phase 2 routes)

# ==================== STUDENT DASHBOARD ====================
# @app.route('/student/dashboard')
# @student_required
# def student_dashboard():
#     student_id = session.get('student_id')
#     stud = Student.query.get(student_id)
    
#     if not stud.class_id:
#         flash('You are not assigned to any class yet. Please contact admin.', 'warning')
#         return render_template('student_dashboard.html', student=stud, stats={})
    
#     # Get student's subjects
#     class_subjects = ClassSubject.query.filter_by(class_id=stud.class_id).all()
    
#     # Calculate attendance percentage
#     total_attendance = Attendance.query.filter_by(student_id=stud.student_id).count()
#     present_count = Attendance.query.filter_by(student_id=stud.student_id, status='Present').count()
#     attendance_percentage = (present_count / total_attendance * 100) if total_attendance > 0 else 0
    
#     # Get pending assignments
#     all_assignments = Assignment.query.filter_by(class_id=stud.class_id).all()
#     submitted_ids = [s.assignment_id for s in stud.submissions]
#     pending_assignments = [a for a in all_assignments if a.id not in submitted_ids and a.due_date >= date.today()]
    
#     # Get recent marks
#     recent_marks = Marks.query.filter_by(student_id=stud.student_id).order_by(Marks.date.desc()).limit(5).all()
    
#     # Get latest notifications
#     notifications = Notification.query.filter_by(class_id=stud.class_id).order_by(Notification.date.desc()).limit(5).all()
    
#     stats = {
#         'attendance_percentage': round(attendance_percentage, 2),
#         'total_subjects': len(class_subjects),
#         'pending_assignments': len(pending_assignments),
#         'total_marks_entries': Marks.query.filter_by(student_id=stud.student_id).count()
#     }
    
#     return render_template('student_dashboard.html',
#                          student=stud,
#                          stats=stats,
#                          recent_marks=recent_marks,
#                          pending_assignments=pending_assignments,
#                          notifications=notifications)

@app.route('/student/dashboard')
@student_required
def student_dashboard():
    student_id = session.get('student_id')
    stud = Student.query.get(student_id)
    
    if not stud.class_id:
        flash('You are not assigned to any class yet. Please contact admin.', 'warning')
        return render_template('student_dashboard.html', 
                             student=stud, 
                             stats={},
                             recent_marks=[],
                             pending_assignments=[],
                             notifications=[])
    
    # Get student's subjects
    class_subjects = ClassSubject.query.filter_by(class_id=stud.class_id).all()
    
    # Calculate attendance percentage
    total_attendance = Attendance.query.filter_by(student_id=stud.student_id).count()
    present_count = Attendance.query.filter_by(student_id=stud.student_id, status='Present').count()
    attendance_percentage = (present_count / total_attendance * 100) if total_attendance > 0 else 0
    
    # Get pending assignments (not submitted and not overdue)
    today = date.today()
    all_assignments = Assignment.query.filter_by(class_id=stud.class_id).all()
    submitted_ids = [s.assignment_id for s in stud.submissions]
    
    # Only assignments that are NOT submitted AND due date is today or future
    pending_assignments = [
        a for a in all_assignments 
        if a.id not in submitted_ids and a.due_date >= today
    ]
    
    # Get recent marks
    recent_marks = Marks.query.filter_by(student_id=stud.student_id).order_by(Marks.date.desc()).limit(5).all()
    
    # Get latest notifications
    notifications = Notification.query.filter_by(class_id=stud.class_id).order_by(Notification.date.desc()).limit(5).all()
    
    stats = {
        'attendance_percentage': round(attendance_percentage, 2),
        'total_subjects': len(class_subjects),
        'pending_assignments': len(pending_assignments),
        'total_marks_entries': Marks.query.filter_by(student_id=stud.student_id).count()
    }
    
    return render_template('student_dashboard.html',
                         student=stud,
                         stats=stats,
                         recent_marks=recent_marks,
                         pending_assignments=pending_assignments,
                         notifications=notifications,
                         today=today)


# ==================== MY SUBJECTS ====================
@app.route('/student/my_subjects')
@student_required
def student_my_subjects():
    student_id = session.get('student_id')
    stud = Student.query.get(student_id)
    
    if not stud.class_id:
        flash('You are not assigned to any class yet!', 'warning')
        return redirect(url_for('student_dashboard'))
    
    class_subjects = ClassSubject.query.filter_by(class_id=stud.class_id).all()
    
    return render_template('student_my_subjects.html',
                         student=stud,
                         class_subjects=class_subjects)


# ==================== ATTENDANCE ====================
@app.route('/student/attendance')
@student_required
def student_attendance():
    student_id = session.get('student_id')
    stud = Student.query.get(student_id)
    
    # Get all attendance records
    attendances = Attendance.query.filter_by(student_id=stud.student_id).order_by(Attendance.date.desc()).all()
    
    # Calculate statistics
    total = len(attendances)
    present = len([a for a in attendances if a.status == 'Present'])
    absent = len([a for a in attendances if a.status == 'Absent'])
    late = len([a for a in attendances if a.status == 'Late'])
    
    attendance_stats = {
        'total': total,
        'present': present,
        'absent': absent,
        'late': late,
        'percentage': round((present / total * 100) if total > 0 else 0, 2)
    }
    
    # Group by subject
    subject_wise = {}
    for att in attendances:
        if att.class_subject:
            subject_name = att.class_subject.subject.name
            if subject_name not in subject_wise:
                subject_wise[subject_name] = {'present': 0, 'absent': 0, 'late': 0, 'total': 0}
            subject_wise[subject_name]['total'] += 1
            subject_wise[subject_name][att.status.lower()] += 1
    
    # Calculate percentage for each subject
    for subject in subject_wise:
        total = subject_wise[subject]['total']
        present = subject_wise[subject]['present']
        subject_wise[subject]['percentage'] = round((present / total * 100) if total > 0 else 0, 2)
    
    return render_template('student_attendance.html',
                         student=stud,
                         attendances=attendances,
                         stats=attendance_stats,
                         subject_wise=subject_wise)


@app.route('/student/attendance/monthly')
@student_required
def student_attendance_monthly():
    """View attendance by month"""
    student_id = session.get('student_id')
    stud = Student.query.get(student_id)
    
    # Get month and year from query params
    month = request.args.get('month', date.today().month, type=int)
    year = request.args.get('year', date.today().year, type=int)
    
    # Get attendance for the month
    attendances = Attendance.query.filter(
        Attendance.student_id == stud.student_id,
        extract('month', Attendance.date) == month,
        extract('year', Attendance.date) == year
    ).order_by(Attendance.date).all()
    
    return render_template('student_attendance_monthly.html',
                         student=stud,
                         attendances=attendances,
                         month=month,
                         year=year)


# ==================== MARKS & PERFORMANCE ====================
@app.route('/student/marks')
@student_required
def student_marks():
    student_id = session.get('student_id')
    stud = Student.query.get(student_id)
    
    # Get all marks
    all_marks = Marks.query.filter_by(student_id=stud.student_id).order_by(Marks.date.desc()).all()
    
    # Group by subject
    subject_wise_marks = {}
    for mark in all_marks:
        subject_name = mark.class_subject.subject.name
        if subject_name not in subject_wise_marks:
            subject_wise_marks[subject_name] = []
        subject_wise_marks[subject_name].append(mark)
    
    # Calculate average for each subject
    subject_averages = {}
    for subject, marks_list in subject_wise_marks.items():
        total_percentage = sum([m.percentage for m in marks_list])
        subject_averages[subject] = round(total_percentage / len(marks_list), 2) if marks_list else 0
    
    # Overall average
    overall_avg = round(sum(subject_averages.values()) / len(subject_averages), 2) if subject_averages else 0
    
    return render_template('student_marks.html',
                         student=stud,
                         all_marks=all_marks,
                         subject_wise_marks=subject_wise_marks,
                         subject_averages=subject_averages,
                         overall_avg=overall_avg)


@app.route('/student/performance')
@student_required
def student_performance():
    """Graphical performance view"""
    student_id = session.get('student_id')
    stud = Student.query.get(student_id)
    
    # Get marks grouped by subject and exam type
    all_marks = Marks.query.filter_by(student_id=stud.student_id).order_by(Marks.date).all()
    
    # Prepare data for charts (will be consumed by frontend JavaScript)
    chart_data = {
        'subjects': [],
        'averages': [],
        'exam_types': {}
    }
    
    # Group by subject
    subject_marks = {}
    for mark in all_marks:
        subject_name = mark.class_subject.subject.name
        if subject_name not in subject_marks:
            subject_marks[subject_name] = []
        subject_marks[subject_name].append(mark)
    
    # Calculate averages
    for subject, marks_list in subject_marks.items():
        chart_data['subjects'].append(subject)
        avg = sum([m.percentage for m in marks_list]) / len(marks_list)
        chart_data['averages'].append(round(avg, 2))
    
    return render_template('student_performance.html',
                         student=stud,
                         chart_data=chart_data)


# ==================== ASSIGNMENTS ====================
# @app.route('/student/assignments')
# @student_required
# def student_assignments():
#     student_id = session.get('student_id')
#     stud = Student.query.get(student_id)
    
#     if not stud.class_id:
#         flash('You are not assigned to any class yet!', 'warning')
#         return redirect(url_for('student_dashboard'))
    
#     # Get all assignments for student's class
#     all_assignments = Assignment.query.filter_by(class_id=stud.class_id).order_by(Assignment.due_date.desc()).all()
    
#     # Categorize assignments
#     pending = []
#     submitted = []
#     graded = []
#     overdue = []
    
#     for assignment in all_assignments:
#         submission = Submission.query.filter_by(
#             assignment_id=assignment.id,
#             student_id=stud.student_id
#         ).first()
        
#         if submission:
#             if submission.status == 'Graded':
#                 graded.append({'assignment': assignment, 'submission': submission})
#             else:
#                 submitted.append({'assignment': assignment, 'submission': submission})
#         else:
#             if assignment.due_date < date.today():
#                 overdue.append(assignment)
#             else:
#                 pending.append(assignment)
    
#     return render_template('student_assignments.html',
#                          student=stud,
#                          pending=pending,
#                          submitted=submitted,
#                          graded=graded,
#                          overdue=overdue)


# @app.route('/student/assignment/<int:assignment_id>')
# @student_required
# def view_assignment(assignment_id):
#     """View assignment details"""
#     student_id = session.get('student_id')
#     stud = Student.query.get(student_id)
    
#     assignment = Assignment.query.get_or_404(assignment_id)
    
#     # Check if student is in this class
#     if assignment.class_id != stud.class_id:
#         flash('Unauthorized access', 'error')
#         return redirect(url_for('student_dashboard'))
    
#     # Check if already submitted
#     submission = Submission.query.filter_by(
#         assignment_id=assignment_id,
#         student_id=stud.student_id
#     ).first()
    
#     return render_template('view_assignment.html',
#                          student=stud,
#                          assignment=assignment,
#                          submission=submission)


# @app.route('/student/submit_assignment/<int:assignment_id>', methods=['GET', 'POST'])
# @student_required
# def submit_assignment(assignment_id):
#     """Submit an assignment"""
#     student_id = session.get('student_id')
#     stud = Student.query.get(student_id)
    
#     assignment = Assignment.query.get_or_404(assignment_id)
    
#     if assignment.class_id != stud.class_id:
#         flash('Unauthorized access', 'error')
#         return redirect(url_for('student_dashboard'))
    
#     # Check if already submitted
#     existing = Submission.query.filter_by(
#         assignment_id=assignment_id,
#         student_id=stud.student_id
#     ).first()
    
#     if existing:
#         flash('You have already submitted this assignment!', 'warning')
#         return redirect(url_for('view_assignment', assignment_id=assignment_id))
    
#     if request.method == 'POST':
#         submission_link = request.form.get('submission_link', '')
        
#         # Handle file upload
#         file_path = None
#         if 'file' in request.files:
#             file = request.files['file']
#             if file and file.filename and allowed_file(file.filename):
#                 filename = secure_filename(file.filename)
#                 filename = f"{stud.student_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
#                 filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'submissions', filename)
#                 file.save(filepath)
#                 file_path = filepath
        
#         # Must have either link or file
#         if not submission_link and not file_path:
#             flash('Please provide either a submission link or upload a file', 'error')
#             return redirect(url_for('submit_assignment', assignment_id=assignment_id))
        
#         # Determine if late
#         status = 'Late' if date.today() > assignment.due_date else 'Submitted'
        
#         new_submission = Submission(
#             assignment_id=assignment_id,
#             student_id=stud.student_id,
#             submission_link=submission_link,
#             file_path=file_path,
#             status=status
#         )
        
#         db.session.add(new_submission)
#         db.session.commit()
        
#         flash('Assignment submitted successfully!', 'success')
#         return redirect(url_for('student_assignments'))
    
#     return render_template('submit_assignment.html',
#                          student=stud,
#                          assignment=assignment)


@app.route('/student/assignments')
@student_required
def student_assignments():
    student_id = session.get('student_id')
    stud = Student.query.get(student_id)
    
    if not stud.class_id:
        flash('You are not assigned to any class yet!', 'warning')
        return redirect(url_for('student_dashboard'))
    
    # Get filter from query params
    filter_type = request.args.get('filter', 'all')
    
    # Get all assignments for student's class
    all_assignments = Assignment.query.filter_by(class_id=stud.class_id).order_by(Assignment.due_date.desc()).all()
    
    # Prepare unified assignment list with submission info
    assignments = []
    today = date.today()
    
    for assignment in all_assignments:
        # Check if student has submitted this assignment
        submission = Submission.query.filter_by(
            assignment_id=assignment.id,
            student_id=stud.student_id
        ).first()
        
        # Determine status and if overdue
        is_overdue = assignment.due_date < today and not submission
        
        if submission:
            status = submission.status  # 'Submitted', 'Graded', 'Late'
        elif is_overdue:
            status = 'Overdue'
        else:
            status = 'Pending'
        
        # Create item dict
        item = {
            'assignment': assignment,
            'submission': submission,
            'status': status,
            'is_overdue': is_overdue
        }
        
        # Apply filter
        if filter_type == 'all':
            assignments.append(item)
        elif filter_type == 'pending' and status == 'Pending':
            assignments.append(item)
        elif filter_type == 'submitted' and submission and submission.status == 'Submitted':
            assignments.append(item)
        elif filter_type == 'graded' and submission and submission.status == 'Graded':
            assignments.append(item)
        elif filter_type == 'overdue' and (status == 'Overdue' or (submission and submission.status == 'Late')):
            assignments.append(item)
    
    return render_template('student_assignments.html',
                         student=stud,
                         assignments=assignments,
                         filter=filter_type,
                         today=today)
@app.route('/student/assignment/<int:assignment_id>')
@student_required
def view_assignment(assignment_id):
    """View assignment details"""
    student_id = session.get('student_id')
    stud = Student.query.get(student_id)
    
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Check if student is in this class
    if assignment.class_id != stud.class_id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('student_dashboard'))
    
    # Check if already submitted
    submission = Submission.query.filter_by(
        assignment_id=assignment_id,
        student_id=stud.student_id
    ).first()
    
    # Check if overdue
    is_overdue = assignment.due_date < date.today()
    
    return render_template('view_assignment.html',
                         student=stud,
                         assignment=assignment,
                         submission=submission,
                         is_overdue=is_overdue,
                         today=date.today())


@app.route('/student/submit_assignment/<int:assignment_id>', methods=['GET', 'POST'])
@student_required
def submit_assignment(assignment_id):
    """Submit an assignment"""
    student_id = session.get('student_id')
    stud = Student.query.get(student_id)
    
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Verify student is in the correct class
    if assignment.class_id != stud.class_id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('student_dashboard'))
    
    # Check if already submitted
    existing = Submission.query.filter_by(
        assignment_id=assignment_id,
        student_id=stud.student_id
    ).first()
    
    if existing:
        flash('You have already submitted this assignment!', 'warning')
        return redirect(url_for('view_assignment', assignment_id=assignment_id))
    
    if request.method == 'POST':
        submission_link = request.form.get('submission_link', '').strip()
        
        # Handle file upload
        file_path = None
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"{stud.student_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'submissions', filename)
                file.save(filepath)
                file_path = filepath
        
        # Must have either link or file
        if not submission_link and not file_path:
            flash('Please provide either a submission link or upload a file', 'error')
            return redirect(url_for('submit_assignment', assignment_id=assignment_id))
        
        # Determine if late
        today = date.today()
        status = 'Late' if today > assignment.due_date else 'Submitted'
        
        new_submission = Submission(
            assignment_id=assignment_id,
            student_id=stud.student_id,
            submission_link=submission_link if submission_link else None,
            file_path=file_path,
            status=status
        )
        
        db.session.add(new_submission)
        db.session.commit()
        
        flash(f'Assignment submitted successfully! Status: {status}', 'success')
        return redirect(url_for('student_assignments'))
    
    # GET request - show form
    is_overdue = assignment.due_date < date.today()
    
    return render_template('submit_assignment.html',
                         student=stud,
                         assignment=assignment,
                         is_overdue=is_overdue,
                         today=date.today())

# ==================== DIARY ====================
@app.route('/student/diary')
@student_required
def student_diary():
    student_id = session.get('student_id')
    stud = Student.query.get(student_id)
    
    if not stud.class_id:
        flash('You are not assigned to any class yet!', 'warning')
        return redirect(url_for('student_dashboard'))
    
    # Get diary entries for student's class
    diaries = Diary.query.filter_by(class_id=stud.class_id).order_by(Diary.date.desc()).all()
    
    return render_template('student_diary.html',
                         student=stud,
                         diaries=diaries)


@app.route('/student/diary/today')
@student_required
def student_diary_today():
    """View today's diary entries"""
    student_id = session.get('student_id')
    stud = Student.query.get(student_id)
    
    today_diaries = Diary.query.filter_by(
        class_id=stud.class_id,
        date=date.today()
    ).all()
    
    return render_template('student_diary_today.html',
                         student=stud,
                         diaries=today_diaries)


# ==================== NOTIFICATIONS ====================
@app.route('/student/notifications')
@student_required
def student_notifications():
    student_id = session.get('student_id')
    stud = Student.query.get(student_id)
    
    if not stud.class_id:
        flash('You are not assigned to any class yet!', 'warning')
        return redirect(url_for('student_dashboard'))
    
    # Get notifications for student's class
    notifications = Notification.query.filter_by(class_id=stud.class_id).order_by(Notification.date.desc()).all()
    
    return render_template('student_notifications.html',
                         student=stud,
                         notifications=notifications)


# ==================== PROFILE ====================
@app.route('/student/profile')
@student_required
def student_profile():
    student_id = session.get('student_id')
    stud = Student.query.get(student_id)
    
    return render_template('student_profile.html', student=stud)


# ==================== API ENDPOINTS FOR STUDENT ====================
@app.route('/api/student/attendance_data')
@student_required
def api_student_attendance_data():
    """API endpoint for attendance chart data"""
    student_id = session.get('student_id')
    stud = Student.query.get(student_id)
    
    attendances = Attendance.query.filter_by(student_id=stud.student_id).all()
    
    # Group by month
    monthly_data = {}
    for att in attendances:
        month_key = att.date.strftime('%Y-%m')
        if month_key not in monthly_data:
            monthly_data[month_key] = {'present': 0, 'absent': 0, 'late': 0}
        monthly_data[month_key][att.status.lower()] += 1
    
    return jsonify(monthly_data)


@app.route('/api/student/marks_data')
@student_required
def api_student_marks_data():
    """API endpoint for marks chart data"""
    student_id = session.get('student_id')
    stud = Student.query.get(student_id)
    
    marks = Marks.query.filter_by(student_id=stud.student_id).all()
    
    # Group by subject
    subject_data = {}
    for mark in marks:
        subject_name = mark.class_subject.subject.name
        if subject_name not in subject_data:
            subject_data[subject_name] = []
        subject_data[subject_name].append({
            'exam_type': mark.exam_type,
            'percentage': mark.percentage,
            'date': mark.date.isoformat()
        })
    
    return jsonify(subject_data)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create default admin
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            default_admin = Admin(
                name='System Administrator',
                username='admin',
                email='admin@sms.com'
            )
            default_admin.set_password('admin123')
            db.session.add(default_admin)
            db.session.commit()
            print('✓ Default admin created: username=admin, password=admin123')
    
    app.run(debug=True)
