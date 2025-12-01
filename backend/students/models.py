from django.db import models
# Create your models here.
class Student(models.Model):
     student_id=models.CharField(max_length=20,unique=True)
     name=models.CharField(max_length=100)
     email=models.EmailField(unique=True)
     enrollment_date=models.DateField()
     


