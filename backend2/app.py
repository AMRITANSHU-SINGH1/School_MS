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


# ==================== MODELS ====================
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
@app.route('/student/dashboard')
@student_required
def student_dashboard():
    student_id = session.get('student_id')
    stud = Student.query.get(student_id)
    
    if not stud.class_id:
        flash('You are not assigned to any class yet. Please contact admin.', 'warning')
        return render_template('student_dashboard.html', student=stud, stats={})
    
    # Get student's subjects
    class_subjects = ClassSubject.query.filter_by(class_id=stud.class_id).all()
    
    # Calculate attendance percentage
    total_attendance = Attendance.query.filter_by(student_id=stud.student_id).count()
    present_count = Attendance.query.filter_by(student_id=stud.student_id, status='Present').count()
    attendance_percentage = (present_count / total_attendance * 100) if total_attendance > 0 else 0
    
    # Get pending assignments
    all_assignments = Assignment.query.filter_by(class_id=stud.class_id).all()
    submitted_ids = [s.assignment_id for s in stud.submissions]
    pending_assignments = [a for a in all_assignments if a.id not in submitted_ids and a.due_date >= date.today()]
    
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
                         notifications=notifications)


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
@app.route('/student/assignments')
@student_required
def student_assignments():
    student_id = session.get('student_id')
    stud = Student.query.get(student_id)
    
    if not stud.class_id:
        flash('You are not assigned to any class yet!', 'warning')
        return redirect(url_for('student_dashboard'))
    
    # Get all assignments for student's class
    all_assignments = Assignment.query.filter_by(class_id=stud.class_id).order_by(Assignment.due_date.desc()).all()
    
    # Categorize assignments
    pending = []
    submitted = []
    graded = []
    overdue = []
    
    for assignment in all_assignments:
        submission = Submission.query.filter_by(
            assignment_id=assignment.id,
            student_id=stud.student_id
        ).first()
        
        if submission:
            if submission.status == 'Graded':
                graded.append({'assignment': assignment, 'submission': submission})
            else:
                submitted.append({'assignment': assignment, 'submission': submission})
        else:
            if assignment.due_date < date.today():
                overdue.append(assignment)
            else:
                pending.append(assignment)
    
    return render_template('student_assignments.html',
                         student=stud,
                         pending=pending,
                         submitted=submitted,
                         graded=graded,
                         overdue=overdue)


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
    
    return render_template('view_assignment.html',
                         student=stud,
                         assignment=assignment,
                         submission=submission)


@app.route('/student/submit_assignment/<int:assignment_id>', methods=['GET', 'POST'])
@student_required
def submit_assignment(assignment_id):
    """Submit an assignment"""
    student_id = session.get('student_id')
    stud = Student.query.get(student_id)
    
    assignment = Assignment.query.get_or_404(assignment_id)
    
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
        submission_link = request.form.get('submission_link', '')
        
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
        status = 'Late' if date.today() > assignment.due_date else 'Submitted'
        
        new_submission = Submission(
            assignment_id=assignment_id,
            student_id=stud.student_id,
            submission_link=submission_link,
            file_path=file_path,
            status=status
        )
        
        db.session.add(new_submission)
        db.session.commit()
        
        flash('Assignment submitted successfully!', 'success')
        return redirect(url_for('student_assignments'))
    
    return render_template('submit_assignment.html',
                         student=stud,
                         assignment=assignment)


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
