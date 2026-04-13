from django.contrib import admin


from .models import Employee, Attendance

# Register your models here.


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):

    list_display = [
        'employee_id',
        'first_name',
        'last_name',
        'department',
        'position',
        'is_active',
        'created_at',
    ]

    list_filter = [
        'is_active',
        'department',
        'created_at',
    ]

    search_fields = [
        'employee_id',
        'first_name',
        'last_name',
        'email',
        'department',
    ]

    ordering = ['employee_id']
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'face_encoding',
    ]

    fieldsets = (
        ("Asosiy ma'lumotlar (Basic information)", {
            'fields':(
                'employee_id',
                'first_name',
                'last_name',
                'email',
            )
        }),

        ("Ish Ma'lumotlari (Work information)",{
            'fields':(
                'department',
                'position',
                'is_active',
            )
        }),

        ("Yuz tanish (Face Recognition)",{
            'fields':(
                'photo',
                'face_encoding',
            )
        }),

        ('Vaqt Belgilari (Timestamps)',{
            'fields':(
                'created_at',
                'updated_at',
            ),
            'classes':('collapse',),
        })
    )

    list_per_page =  25

    date_hierarchy = 'created_at'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = [
        'employee',
        'date',
        'check_in_time',
        'check_out_time',
        'status', 
        'get_work_duration',

    ]

    list_filter = [
        'status',
        'date',
        'employee__department',

    ]

    search_fields = [
        'employee__employee_id',
        'employee__first_name',
        'employee__last_name',
        'notes',
    ]

    ordering = ['-date', '-check_in_time']


    readonly_fields = [
        'created_at',
        'updated_at',
    ]

    fieldsets = (
        ("Davomat Ma'lumotlari (Attendance Information)", {
            'fields':(
                'employee',
                'date',
                'status',
            )
        }),

        ("Vaqt yozuvlari (Time Records)",{
            'fields':(
                'check_in_time',
                'check_out_time',
            )
        }),

        ("Izohlar (Notes)",{
            'fields':(
                'notes',
            )
        }),

        ('Vaqt Belgilari (Timestamps)',{
            'fields':(
                'created_at',
                'updated_at',
            ),
            'classes':('collapse',),
        })
    )

    list_per_page = 50


    date_hierarchy = 'date'



    raw_id_fields = ['employee']

    admin.site.site_header = 'Yuz Tanish Davomat Tizimi (Face Recognition Attendance)'


    admin.site.site_title =  'Davomat Admin'



    admin.site.index_title =  'Boshqaruv Paneli (Admin Panel)'


