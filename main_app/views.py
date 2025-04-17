import json,requests
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from .EmailBackend import EmailBackend
from django.utils import timezone
from datetime import date
from .forms import *
from .models import *



def login_page(request):
    if request.user.is_authenticated:
        if request.user.user_type == '1':
            return redirect(reverse("admin_home"))
        elif request.user.user_type == '2':
            return redirect(reverse("manager_home"))
        else:
            return redirect(reverse("employee_home"))
    return render(request, 'main_app/login.html')


def doLogin(request, **kwargs):
    if request.method != 'POST':
        return HttpResponse("<h4>Denied</h4>")
    else:
        captcha_token = request.POST.get('g-recaptcha-response')
        captcha_url = "https://www.google.com/recaptcha/api/siteverify"
        captcha_key = "6LcccxsrAAAAAOe4_jxUb9yj1Tu4gqxaIG5U_HCh"
        data = {
            'secret': captcha_key,
            'response': captcha_token
        }
        try:
            captcha_server = requests.post(url=captcha_url, data=data)
            response = json.loads(captcha_server.text)
            if response['success'] == False:
                messages.error(request, 'Invalid Captcha. Try Again')
                return redirect('/')
        except:
            messages.error(request, 'Captcha could not be verified. Try Again')
            return redirect('/')
        
        user = authenticate(request, username=request.POST.get('email'), password=request.POST.get('password'))
        if user != None:
            login(request, user)
            if user.user_type == '1':
                return redirect(reverse("admin_home"))
            elif user.user_type == '2':
                return redirect(reverse("manager_home"))
            else:
                return redirect(reverse("employee_home"))
        else:
            messages.error(request, "Invalid details")
            return redirect("/")



def logout_user(request):
    if request.user != None:
        logout(request)
    return redirect("/")


def clock_action(request):
    if request.method != "POST":
        return redirect('home')  

    clock_action = request.POST.get('clock_action', '')
    user = request.user

    home_route = {
        '2': 'manager_home',
        '3': 'employee_home'
    }.get(user.user_type, 'home')
    home = redirect(reverse(home_route))

    custom_user = get_object_or_404(CustomUser, id=user.id, user_type=user.user_type)
    now = timezone.now()
    ip_address = request.META.get('REMOTE_ADDR', 'NA')

    try:
        last_entry = Timesheet.objects.filter(custom_user=custom_user).latest('clocking_time')
    except Timesheet.DoesNotExist:
        last_entry = None

    if clock_action == "ClockIn":
        if not last_entry or last_entry.logging == "OUT":
            Timesheet.objects.create(
                custom_user=custom_user,
                recorded_by=custom_user,
                recorded_datetime=date.today(),
                clocking_time=now,
                logging="IN",
                ip_address=ip_address
            )
        else:
            messages.error(request, "You must clock out before you can clock in.")
    
    elif clock_action == "ClockOut":
        if last_entry and last_entry.logging == "IN":
            delta_hours = (now - last_entry.clocking_time).total_seconds() / 3600.0
            max_hours, min_hours_required = 12, 8

            if delta_hours < max_hours:
                Timesheet.objects.create(
                    custom_user=custom_user,
                    recorded_by=custom_user,
                    recorded_datetime=date.today(),
                    clocking_time=now,
                    logging="OUT",
                    ip_address=ip_address
                )

                attendance_date = last_entry.clocking_time.date()
                department = (custom_user.employee.department 
                              if user.user_type == '3' 
                              else custom_user.manager.department)
                
                attendance, _ = Attendance.objects.get_or_create(
                    date=attendance_date,
                    department=department
                )

                if delta_hours >= min_hours_required:
                    AttendanceReport.objects.get_or_create(
                        attendance=attendance,
                        custom_user=custom_user,
                        defaults={'status': True}
                    )
            else:
                messages.error(request, f"You cannot clock out more than {max_hours} hours after clocking in.")
        else:
            messages.error(request, "You must clock in before you can clock out.")
    else:
        messages.error(request, "Invalid action.")

    return home


@csrf_exempt
def get_attendance(request):
    department_id = request.POST.get('department')
    try:
        department = get_object_or_404(Department, id=department_id)
        attendance = Attendance.objects.filter(department=department)
        
        attendance_list = []
        for attd in attendance:
            data = {
                    "id": attd.id,
                    "attendance_date": str(attd.date)
                    }
            attendance_list.append(data)
        return JsonResponse(json.dumps(attendance_list), safe=False)
    except Exception as e:
        return None


def showFirebaseJS(request):
    data = """
    // Give the service worker access to Firebase Messaging.
// Note that you can only use Firebase Messaging here, other Firebase libraries
// are not available in the service worker.
importScripts('https://www.gstatic.com/firebasejs/7.22.1/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/7.22.1/firebase-messaging.js');

// Initialize the Firebase app in the service worker by passing in
// your app's Firebase config object.
// https://firebase.google.com/docs/web/setup#config-object
firebase.initializeApp({
    apiKey: "AIzaSyBarDWWHTfTMSrtc5Lj3Cdw5dEvjAkFwtM",
    authDomain: "sms-with-django.firebaseapp.com",
    databaseURL: "https://sms-with-django.firebaseio.com",
    projectId: "sms-with-django",
    storageBucket: "sms-with-django.appspot.com",
    messagingSenderId: "945324593139",
    appId: "1:945324593139:web:03fa99a8854bbd38420c86",
    measurementId: "G-2F2RXTL9GT"
});

// Retrieve an instance of Firebase Messaging so that it can handle background
// messages.
const messaging = firebase.messaging();
messaging.setBackgroundMessageHandler(function (payload) {
    const notification = JSON.parse(payload);
    const notificationOption = {
        body: notification.body,
        icon: notification.icon
    }
    return self.registration.showNotification(payload.notification.title, notificationOption);
});
    """
    return HttpResponse(data, content_type='application/javascript')

