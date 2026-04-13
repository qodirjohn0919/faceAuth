from django.urls import path



from . import views


urlpatterns = [

    path (
        '',
        views.home,
        name = 'home'
    ),

    path(
        'employees/',
        views.employee_list,
        name = 'employee_list'
    ),

    path(
        'register/',
        views.register_employee,
        name = 'register_employee'
    ),

    path(
        'employee/<str:employee_id>/',
        views.employee_detail,
        name =  'employee_detail'
    ),


    path ( 
        'employee/<str:employee_id>/delete/',
        views.delete_employee,
        name='delete_employee'
    ),

    path(
        'attendance/',
        views.mark_attendance,
        name = 'mark_attendance'
    ),


    path(
        'api/process-attendance/',
        views.process_attendance,
        name='process_attendance'
    ),

    path (
        'today/',
        views.today_attendance,
        name='today_attendance'
    ),

    path(
        'reports/',
        views.attendance_list,
        name = 'attendance_list'
    )





]