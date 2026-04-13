from django.shortcuts import render

# Create your views here.
from django.shortcuts import render,redirect, get_object_or_404

from django.http import JsonResponse, HttpResponse

from django.contrib import messages

from django.utils import timezone

from datetime import date, datetime, time, timedelta

import json

from django.db.models import Count, Q

from django.views.decorators.csrf import csrf_exempt

from .models import Employee, Attendance

from . import face_utils


def home(request):
    total_employees = Employee.objects.filter(is_active=True).count()

    today = date.today()

    today_attendance = Attendance.objects.filter(date=today).count()

    checked_in_today = Attendance.objects.filter(
        date = today,
        check_in_time__isnull = False
    ).count()

    check_out_today = Attendance.objects.filter(
        date=today,
        check_out_time__isnull = False
    ).count()

    recent_attendance = Attendance.objects.select_related('employee').order_by(
        '-date', '-check_in_time'
    )[:10]

    not_checked_in = total_employees - checked_in_today

    context = {
        'total_employees': total_employees,
        'today_attendance': today_attendance,
        'checked_in_today': checked_in_today,
        'checked_out_today': check_out_today,
        'recent_attendance': recent_attendance,
        'today': today,
        'not_checked_in': not_checked_in,
    }

    return render(request, 'home.html', context)


def employee_list(request):
    employees = Employee.objects.filter(is_active=True).order_by('employee_id')

    context = {
        'employees': employees
    }

    return render(request, 'employee_list.html', context)


def register_employee(request):
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        department = request.POST.get('department', '').strip() or None 
        position = request.POST.get('position', '').strip() or None

        face_image_data = request.POST.get('face_image', '')

        errors = []

        if not employee_id:
            errors.append(' Xodim ID kiritilishi shart (Employee ID is required )')
        
        if not first_name:
            errors.append(
                'Ism kiritilishi shart (First name is required) '
            )
        
        if not last_name:
            errors.append(
                'Familiya kiritish shart (Last name is required )'
            )

        if not face_image_data:
            errors.append('Yuz rasmi olinishi shart (Face photo is required)')

        if employee_id and Employee.objects.filter(employee_id=employee_id).exists():
            errors.append(f"Xodim ID {employee_id} allaqachon mavjud (Employee ID already exists)")
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'register_employee.html')
        
        image = face_utils.process_base64_image(face_image_data)

        if image is None:
            messages.error(request, 'Rasm qayta ishlanmadi (Could not process image )')
            return render(request, 'register_employee.html')
        
        validation = face_utils.validate_face_image(image)

        if not validation['valid']:
            messages.error(request, validation['message'])
            return render(request, 'register_employee.html')
        





        face_encoding = face_utils.get_face_encoding(image, validation['face_location'])

        if face_encoding is None:
            messages.error(request, 'Yuz kodlashi olinmadi (Could not get face encoding )')
            return render(request, 'register_employee.html')
        

        image_path = face_utils.save_face_image(image, employee_id)

        if image_path is None:
            messages.error(request, 'Rasm saqlanmadi (Could not save image )')
            return render(request, 'register_employee.html')
        

        employee = Employee(
            employee_id = employee_id,
            first_name = first_name,
            last_name = last_name,
            email = email,
            department = department,
            position = position,
            photo = image_path
        )
        
        employee.set_face_encoding(face_encoding)

        employee.save()

        messages.success(
            request,
            f"Xodim {employee.full_name()} muvaffaqiyatli ro'yxatdan o'tkazildi! "
            f"Employee {employee.full_name()} registered successfully ! "
        )

        return redirect(
            'employee_list'
        )
    return render(request, 'register_employee.html')


def mark_attendance(request):
    return render(request, 'mark_attendance.html')


@csrf_exempt
def process_attendance(request):
    if request.method != 'POST':
        return JsonResponse({
            'success':False,
            'message': 'Faqat POST so\'rovlari qabul qilindi (Only POST requests allowed)'
        }, status=405)
    
    try:
        data = json.loads(request.body)
        face_image_data = data.get('face_image', '')
        action =  data.get('action', 'check_in')

        if not face_image_data:
            return JsonResponse({
                'success': False,
                'message': 'Yuz rasmi kerak (Face image required)'
            })
        image = face_utils.process_base64_image(face_image_data)

        if image is None:
            return JsonResponse({
                'success': False,
                'message': 'Rasm qayta ishlamadi (Could not process image)'
            })
        
        validation  = face_utils.validate_face_image(image)


        if not validation['valid']:
            return JsonResponse({
                'success':False,
                'message':validation['message']
            })
        
        unknown_encoding = face_utils.get_face_encoding(image, validation['face_location'])

        if unknown_encoding is None:
            return JsonResponse({
                'success': False,
                'message': 'Yuz kodlash olinmadi ( Could not get face encoding)'
            })
        
        employees = Employee.objects.filter(is_active= True)

        if not employees.exists():
            return JsonResponse({
                'success':False,
                'message': "Ro'yxatdan o'tgan xodimlar yo'q ( No registered employee)"
            })
        
        matched_employee, distance = face_utils.find_matching_employee(
            unknown_encoding,
            employees
        )

        if matched_employee is None:
            return JsonResponse({
                'success':False,
                'message': 'Yuz tanilmadi. Iltimos, avval ro\'yxatdan o\'ting.'
            })
        
        today = date.today()

        current_time = timezone.localtime().time()

        attendance, created = Attendance.objects.get_or_create(
            employee = matched_employee,
            date = today,
            defaults= {
                'check_in_time':current_time if action == 'check_in' else None,
                'status' : 'present'
            }
        )
        if action == 'check_in':
            if attendance.check_in_time and not created:
                return JsonResponse({
                    'success': False,
                    'message': f"{matched_employee.full_name()} bugun allaqachon kirgan "
                               f'({attendance.check_in_time.strftime("%H:%M")})'
                               f'(Already checked today)'
                })
            attendance.check_in_time = current_time

            work_start = time ( 9, 0,  0)

            if current_time > work_start:
                attendance.status = 'late'
                status_msg = 'Kechikdi (Late)'
            else:
                attendance.status = 'present'
                status_msg = "O'z vaqtida (On time )"
            
            attendance.save()

            return JsonResponse({
                'success': True,
                'message': f"Kirish belgilandi: {matched_employee.full_name()} - "
                           f'{current_time.strftime("%H:%M")} ({status_msg}). '
                           f"(Check - in recorded)",
                'employee':{
                    'id': matched_employee.id,
                    'employee_id': matched_employee.employee_id,
                    'name':matched_employee.full_name(),
                    'department': matched_employee.department,
                    'time': current_time.strftime("%H:%M:%S"),
                    'status': attendance.status,
                    'distance': round(distance, 4)
                }
            })
        elif action == 'check_out':
            if not attendance.check_in_time:
                return JsonResponse({
                    'success':False,
                    'message': f"{matched_employee.full_name()} Bugun kirish qilmagan. "
                               f"(No check - in record for today)"
                })
            
            if attendance.check_out_time:
                return JsonResponse({
                    'success':False,
                    'message': f"{matched_employee.full_name()} bugun allaqachon chiqgan"
                               f"({attendance.check_out_time.strftime('%H:%M')})"
                               f"(Already checked out today)"
                })
            
            attendance.check_out_time = current_time

            attendance.save()

            work_duration = attendance.get_work_duration()

            return JsonResponse({
                'success':True,
                'message': f"chiqish belgilandi : {matched_employee.full_name()} - "
                           f"{current_time.strftime('%H:%M')}."
                           f"Ish vaqtida : {work_duration}."
                           f"(Checked-out recorded)",
                'employee':{
                    'id': matched_employee.id,
                    'employee_id':matched_employee.employee_id,
                    'name':matched_employee.full_name(),
                    'department':matched_employee.department,
                    'check_in': attendance.check_in_time.strftime("%H:%M:%S"),
                    'check_out': current_time.strftime("%H:%M:%S"),
                    'duration': work_duration,
                    'distance': round(distance, 4)
                }
            })
    except json.JSONDecodeError:
        return JsonResponse({
            'success':False,
            'message': "Noto'g'ri JSON formati (Invalid JSON format)"
        }, status =  400)
    except Exception as e:
        return JsonResponse({
            'success':False,
            'message':f"Xato yuz berdi: {str(e)} (An error occured)"
        }, status = 500)


def attendance_list(request):
    filter_date = request.GET.get('date', '')
    filter_employee = request.GET.get('employee_id', '')
    filter_status = request.GET.get('status', '')

    attendances = Attendance.objects.select_related(
        'employee'
    ).all()


    if filter_date:
        try:
            parsed_date = datetime.strptime(filter_date, '%Y-%m-%d').date()
            attendances = attendances.filter(date=parsed_date)
        
        except ValueError:
            messages.warning(request, "Noto'g'ri sana formati (Invalid date format)")
    
    if filter_employee:
        attendances = attendances.filter(employee__employee_id__icontains=filter_employee)

    if filter_status:
        attendances =  attendances.filter(status=filter_status)

    
    attendances = attendances.order_by('-date',  '-check_in_time')

    available_dates =Attendance.objects.values_list('date', flat=True).distinct().order_by('-date')[:30]

    employees = Employee.objects.filter(is_active=True).order_by('employee_id')

    context = {
        'attendances':attendances,
        'filter_date': filter_date,
        'filter_employee': filter_employee,
        'filter_status': filter_status,
        'available_dates': available_dates,
        'employees': employees,
        'status_choices': Attendance.STATUS_CHOICES,
    }

    return render(request, 'attendance_list.html', context)


def employee_detail(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)

    attendances = employee.attendance.order_by('-date')[:30]

    total_days = employee.attendance.count()
    present_days = employee.attendance.filter(status='present').count()
    late_days = employee.attendance.filter(status='late').count()
    absent_days = employee.attendance.filter(status='absent').count()


    context = {
        'employee': employee,
        'attendances':attendances,
        'total_days': total_days,
        'present_days':present_days,
        'late_days':late_days,
        'absent_days':absent_days,
    }

    return render(request, 'employee_detail.html', context)


def delete_employee(request, employee_id):
    if request.method == 'POST':
        employee = get_object_or_404(Employee, employee_id=employee_id)

        employee.is_active = False
        employee.save()

        messages.success(
            request,
            f"Xodim {employee.full_name()} o'chirildi (Employee deleted)"
        )

        return redirect('employee_list')

    return redirect('employee_list')


def today_attendance(request):
    today = date.today()

    employees = Employee.objects.filter(is_active = True).order_by('employee_id')

    today_records = Attendance.objects.filter(date=today).select_related('employee')

    attendance_dict = {record.employee_id:record for record in today_records}

    employee_attendance = []

    for employee in employees:
        attendance = attendance_dict.get(employee.id)
        employee_attendance.append({
            'employee':employee,
            'attendance':attendance,
            'status': attendance.status if attendance else "Hali kelmagan (Not Arrived))",
            'check_in': attendance.check_in_time if attendance else None,
            'check_out': attendance.check_out_time if attendance else None,
        
        })
    
    total_employees = len(employees)
    checked_in_count = len([ea for ea in employee_attendance if ea['check_in']])
    checked_out_count = len([ea for ea in employee_attendance if ea['check_out']])

    context = {
        'today': today,
        'employee_attendance': employee_attendance,
        'total_employees': total_employees,
        'checked_in': checked_in_count,
        'checked_out': checked_out_count,
        'not_arrived': total_employees - checked_in_count,
    }

    return render(request, 'today_attendance.html', context)
