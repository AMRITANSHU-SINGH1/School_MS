from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
# Create your models here.
class Student(models.Model):
     # Authentiacation and Identity 
     user=models.OneToOneField(User,on_delete=models.CASCADE,null=True,blank=True)
     #student information
     student_id=models.CharField(max_length=20,unique=True) # this is same as enrollement no 
     year_of_join=models.IntegerField()
     admission_date=models.DateField()

     # =============BASIC DETAILS +==============
     first_name=models.CharField(max_length=50)
     last_name=models.CharField(max_length=50)
     dob=models.DateField()
     gender=models.CharField(max_length=10,choices=[('M','Male'),('F','Female'),('O','Other')])
     
     
     #================CONTACT INFORMATION=============
     email=models.EmailField(blank=True,null=True)
     phone=models.CharField(max_length=15)
     address=models.TextField()
     city=models.CharField(max_length=50)
     state=models.CharField(max_length=50)
     pincode=models.CharField(max_length=10)

     #===================parent/guardian==================
     parent_name=models.CharField(max_length=100)
     parent_relationship=models.CharField(max_length=20,choices=[('Father','Father'),('Mother','Mother'),('Guardian','Guardian')],default='Father')
     parent_phone=models.CharField(max_length=15)
     parent_email=models.EmailField()
          #===============emergency===========
     emergency_contact_name = models.CharField(max_length=100, blank=True)
     emergency_contact_phone = models.CharField(max_length=15, blank=True)
     emergency_contact_relationship = models.CharField(max_length=50, blank=True)
     #===============Status================
     is_active=models.BooleanField(default=True)
     status = models.CharField(max_length=20, choices=[
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Suspended', 'Suspended'),
        ('Graduated', 'Graduated'),
        ('Transferred', 'Transferred')
     ], default='Active')
     
     # ==== OPTIONS AVAILABLE FOR THE STUDENT/PATIENT
     email_notifications = models.BooleanField(default=True)
     sms_notifications = models.BooleanField(default=True)
     parent_notifications = models.BooleanField(default=True)


     #==================Only for the future developmet
     created_at = models.DateTimeField(auto_now_add=True)
     updated_at = models.DateTimeField(auto_now=True)
     last_login = models.DateTimeField(null=True, blank=True)

     def save(self,*args,**kwargs):
          if not self.student_id:
               year=self.admission_date.year
               count=Student.objects.filter(admission_date__year=year).count()+1
               self.student_id=f"STU{year}-{count:04d}"
               super().save(*args,**kwargs)

     #=============PROPERTIES===================
     @property
     def full_name(self):
          return f"{self.first_name} {self.last_name}"
    
     @property
     def age(self):
          from datetime import date
          today = date.today()
          return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))
    
     @property
     def admission_number(self):
          """Alias for student_id - same thing"""
          return self.student_id
    
    # ============ STRING REPRESENTATION ============
     def __str__(self):
          return f"{self.student_id} - {self.full_name}"
    
    # ============ META OPTIONS ============
     class Meta:
          ordering = ['admission_date', 'student_id']
          indexes = [
               models.Index(fields=['student_id']),
               models.Index(fields=['admission_date']),
        ]


          

