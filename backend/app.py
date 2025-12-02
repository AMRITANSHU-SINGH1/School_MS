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
     # head_id=db.Column(db.String(100))  #this input should be the doctor id 
     # class_id=db.Column(db.String(20),db.ForeignKey('class.dpt_id'))

class Teacher(db.Model):
     id=db.Column(db.Integer,primary_key=True)
     teacher_id=db.Column(db.String(20),unique=True)
     name=db.Column(db.String(100),nullable=False)
     # dept_id=db.Column(db.String(20),db.ForeignKey('department.dpt_id'))
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
    





