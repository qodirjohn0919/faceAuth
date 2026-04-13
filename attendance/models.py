from django.db import models

# Create your models here.
from django.utils import timezone

from datetime import date, datetime, time 

import json


class Employee(models.Model):
    employee_id = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Xodim ID raqami",
        help_text="Xodimning yagona identifikatsiya raqami"
    )

    first_name = models.CharField(max_length=100, verbose_name="Ism", help_text="Xodimning ismi")

    last_name = models.CharField(max_length=100, verbose_name="Familiya", help_text="Xodimning familiyasi")

    email = models.EmailField(
        max_length=100,
        blank=True,
        verbose_name="Elektron pochta",
        help_text="Xodimning elektron pochta manzili"
    )
    
    department = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Bo'lim",
        help_text="Xodim ishlaydigan bo'lim nomi"
    )

    position = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Lavozim",
        help_text="Xodimning lavozimi"
    )

    photo  =  models.ImageField(
        upload_to='faces/',
        verbose_name="Rasm",
        help_text="Xodimning rasmi",
    )

    face_encoding = models.TextField(
        blank=True,
        null=True,
        verbose_name="Yuz kodlash",
        help_text="Xodimning yuz kodlash ma'lumotlari JSON formatida",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Faol",
        help_text="Xodim faol yoki yo'qligini ko'rsatadi"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Yaratilgan vaqti",
       
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Yangilangan vaqti",
    )

    class Meta:
        db_table = "attendance_employee"

        verbose_name = "Xodim"
        verbose_name_plural = "Xodimlar"

        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee_id} - {self.first_name} - {self.last_name}"
    

    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_face_encoding_list(self):
        if self.face_encoding:
            try:
              return json.loads(self.face_encoding)
            except json.JSONDecodeError:
             return None
        return None
    
    def set_face_encoding(self, encoding_list):
        if encoding_list is not None:
            if hasattr(encoding_list, 'tolist'):
                encoding_list = encoding_list.tolist()
            self.face_encoding = json.dumps(encoding_list)

class Attendance(models.Model):
   STATUS_CHOICES = [
      ('present', 'Keldi (Present)'),
      ('late', 'Kechikdi (Late)'),
      ('absent', 'Kelmadi (Absent)'),
      ('half_day', 'Yarim Kun (half-day)'),
      ('on_leave', 'Ta\'tilda (On Leave)')
   ]

   employee = models.ForeignKey(
      Employee,
      on_delete=models.CASCADE,
      related_name= 'attendance',
      verbose_name= 'Xodim',
      help_text = 'The employee this attendance record belongs to'
   )

   date = models.DateField(
      default=date.today,
      verbose_name="Sana",
      help_text = 'Date of this attendance record'

   )

   check_in_time = models.TimeField(
      blank= True,
      null = True,
      verbose_name= "Kirish vaqti",
      help_text = "Time when employee checked in"
   )

   check_out_time = models.TimeField(
      blank=True,
      null=True,
      verbose_name= 'Chiqish vaqti',
      help_text= 'Time when employee checked out'
   )
   
   status = models.CharField(
      max_length=20,
      choices =  STATUS_CHOICES,
      default= 'present',
      verbose_name='Holat (status)',
      help_text = "Attendance status"
   )

   notes = models.TextField(
      blank=True,
      null=True,
      verbose_name= 'Izohlar',
      help_text= 'Additional notes about this attendance'
   )

   created_at =  models.DateTimeField(
      auto_now_add=True,
      verbose_name='Yaratilgan vaqt (Created At)'
   )

   updated_at = models.DateTimeField(
      auto_now=True,
      verbose_name='Yangilangan vaqti (Updated At)'
   )

   class Meta:
      db_table = 'attendance_attendance'
      verbose_name = "Davomat (Attendance)"
      verbose_name_plural =  'Davomatlar'

      ordering = ['-date', 'check_in_time']

      unique_together = ['employee', 'date']

   def __str__(self):
       return f"{self.employee.full_name()} - {self.date} ({self.get_status_display()})"
   

   def get_work_duration(self):
      if self.check_in_time and self.check_out_time:
         check_in = datetime.combine(self.date, self.check_in_time)
         check_out = datetime.combine(self.date, self.check_out_time)

         duration = check_out -  check_in

         hours =  duration.seconds // 3600
         minutes = (duration.seconds % 3600 ) // 60

         return f"{hours} soat  {minutes} daqiqa ({hours}h {minutes}m)"   
      return "Chiqish belgilanmagan (Not checked out)"   
    
   def is_late(self):
      if self.check_in_time:
         work_start = time (9, 0, 0)
         return self.check_in_time > work_start
      return False
   
   def left_early(self):
      if self.check_out_time:
         work_end =  time(18, 0,  0)
         return self.check_out_time < work_end
      return False
   
      
      



