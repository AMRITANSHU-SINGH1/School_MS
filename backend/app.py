from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import render_template,request,redirect,url_for
from flask import render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash,check_password_hash
from functools import wraps
from flask import session,flash,redirect,url_for
from datetime import date,datetime,timedelta,timezone
'''----IMPORTED ALL THE IMPORTANT THINGS------ '''
app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///SMS.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db=SQLAlchemy(app)
app.secret_key = 'your-secret-key-here-change-in-production'

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_type') != 'admin' or 'admin_id' not in session:
            flash('Please login as admin first')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'teacher_id' not in session:
            flash('Please login as teacher first')
            return redirect(url_for('teacher_login'))
        return f(*args, **kwargs)
    return decorated_function


def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'student_id' not in session:
            flash('Please login as student first')
            return redirect(url_for('student_login'))
        return f(*args, **kwargs)
    return decorated_function


'''-----------MODELS------------------------------'''
class Admin(db.Model):
     id = db.Column(db.Integer, primary_key=True)
     name = db.Column(db.String(100), nullable=False)
     #below are the updates for the admin
     username=db.Column(db.String(50),unique=True)
     email = db.Column(db.String(120), unique=True, nullable=False)   
     password_hash = db.Column(db.String(128), nullable=False)

     def set_password(self,password):
          self.password_hash=generate_password_hash(password)
     
     def check_password(self, password):
          return check_password_hash(self.password_hash, password)

class Subject(db.Model):
     id=db.Column(db.Integer,primary_key=True)
     subject_id=db.Column(db.String(20),unique=True)
     name=db.Column(db.String(100),nullable=False)
     # specialization=db.Column(db.String(100))
     # head_id=db.Column(db.String(100))  #this input should be the teacher id 
     # class_id=db.Column(db.String(20),db.ForeignKey('class.dpt_id'))

class Teacher(db.Model):
     id=db.Column(db.Integer,primary_key=True)
     teacher_id=db.Column(db.String(20),unique=True)
     name=db.Column(db.String(100),nullable=False)
     subject_id=db.Column(db.String(20),db.ForeignKey('Subject.subject_id'))
     status=db.Column(db.String(20),default="Active")
     email = db.Column(db.String(120), unique=True, nullable=False)    
     password_hash = db.Column(db.String(128), nullable=False)
     def set_password(self, password):
          self.password_hash = generate_password_hash(password)

     def check_password(self, password):
          return check_password_hash(self.password_hash, password)

class Student(db.Model):
     id = db.Column(db.Integer, primary_key=True)
     student_id=db.Column(db.String(20),unique=True)
     name = db.Column(db.String(100), nullable=False)
     age=db.Column(db.Integer,nullable=False)
     class_id=db.Column(db.String(20),db.ForeignKey('CLASS.class_id'))
     gender=db.Column(db.String(20),nullable=False)
     contact_info = db.Column(db.Integer,nullable=False)
     parent= db.Column(db.String(100), nullable=False)
     #update after version 1
     email = db.Column(db.String(120), unique=True, nullable=False)  
     password_hash = db.Column(db.String(128), nullable=False)      
     def set_password(self, password):
               self.password_hash = generate_password_hash(password)
     def check_password(self, password):
               return check_password_hash(self.password_hash, password)

class CLASS(db.Model):
     id=db.Column(db.Integer,primary_key=True)
     class_id=db.Column(db.String(20),unique=True)
     name=db.Column(db.String(100), nullable=False)
     head=db.Column(db.String(20),db.ForeignKey('Teacher.teacher_id'),unique=True)


class Diary(db.Model):
#     __tablename__ = 'prescription'
    id = db.Column(db.Integer, primary_key=True)
#     appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)
    teacher_id = db.Column(db.String(20), db.ForeignKey('Teacher.teacher_id'), nullable=False)
    class_id = db.Column(db.String(20), db.ForeignKey('CLASS.teacher_id'), nullable=False)
    
    # Prescription details
    notes = db.Column(db.String(500), nullable=False)
    instructions = db.Column(db.String(500), nullable=False)
    
    
    # Timestamps
    date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda:datetime.now(timezone.utc))
    
    # Relationships

'''------------------LOGIN ROUTES--------------------'''
@app.route('/admin/login',methods=['GET','POST'])
def admin_login():
     if request.method=='POST':
          username=request.form['username']
          password=request.form['password']

          admin=Admin.query.filter_by(username=username).first()

          if admin and admin.check_password(password):
               session['admin_id']=admin.id
               session['user_type']='admin'
               flash('Login successful!')
               return redirect(url_for('admin_dashboard'))
          else:
               flash('Invalid username or password')

     return render_template('admin_login.html')

@app.route('/teacher/login',methods=['GET','POST'])
def teacher_login():
     if request.method=='POST':
          email=request.form['email']
          password=request.form['password']

          teacher=Teacher.query.filter_by(email=email).first()
          if teacher and teacher.check_password(password) and teacher.status=='Active':
               session['teacher_id']=teacher.id
               session['user_type']='teacher'
               flash('Login successfull!')
               return redirect(url_for('teacher_dashboard'))
          else:
               flash('Invalid email or password or teacher is InActive')
     return render_template('teacher_login.html')

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
     if request.method == 'POST':
          email = request.form['email']
          password = request.form['password']

          student = Student.query.filter_by(email=email).first()

          if student and student.check_password(password):
               session['student_id'] = student.id
               session['user_type'] = 'student'
               flash('Login successful!')
               return redirect(url_for('student_dashboard'))
          else:
               flash('Invalid email or password')

     return render_template('student_login.html')


@app.route('/logout')
def logout():
     user_type=session.get('user_type')
     session.clear()
     flash('You have been logged out')

     if user_type=='admin':
          return redirect(url_for('admin_login'))
     elif user_type=='teacher':
          return redirect(url_for('teacher_login'))
     else:
          return redirect(url_for('student_login'))
     
'''------------------------ADMIN FEATURES-----------------------------'''

@app.route('/add_teacher', methods=['GET', 'POST'])
@admin_required
def add_teacher():
     subjects=Subject.query.all()
     if request.method=='POST':
          name=request.form['name']
          email=request.form['email']   #added the email
          password=request.form['password'] #added the password
          subject_id=request.form['subject_id']

          #check for if the email already existed or not 

          existing_teacher=Teacher.query.filter_by(email=email).first()

          if existing_teacher:
               flash("email already registered")
               return redirect(url_for('add_teacher'))

          new_teacher=Teacher(name=name,subject_id=subject_id,email=email)

          new_teacher.set_password(password)
          db.session.add(new_teacher)
          db.session.commit()

          new_teacher.teacher_id=f'TCH_{new_teacher.id:03d}'
          db.session.commit()

          flash('teacher added succesfully')
          # return redirect(url_for('list_teachers'))
     return render_template('add_teacher.html',subjects=subjects)

@app.route('/teachers')
@admin_required
def list_teachers():
     teachers = Teacher.query.all()
     subjects=Subject.query.all()
     return render_template('list_teachers.html',teachers=teachers)






















if __name__=='__main__':
     with app.app_context():
          db.create_all()

          #create the default admin

          admin=Admin.query.filter_by(username='admin').first()
          if not admin:
               default_admin=Admin(name='System Administrator',
                                   username='admin',
                                   email='admin@SMS.com')
               default_admin.set_password('admin123')
               db.session.add(default_admin)
               db.session.commit()
               print('Default admin created: username=admin,password=admin123')
     app.run(debug=True)
