from .models import CustomUser, Timesheet
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser

def clock_times(request):
    context = {
        'latest_clockin': None,
        'latest_clockout': None
    }

    user = request.user
    if isinstance(user, AnonymousUser) or not user.is_authenticated:
        return context

    try:
        custom_user = CustomUser.objects.get(id=user.id)

        last_clockin = Timesheet.objects.filter(custom_user=custom_user, logging="IN").order_by('-clocking_time').first()
        last_clockout = Timesheet.objects.filter(custom_user=custom_user, logging="OUT").order_by('-clocking_time').first()

        context['latest_clockin'] = last_clockin.clocking_time if last_clockin else None
        context['latest_clockout'] = last_clockout.clocking_time if last_clockout else None
    except CustomUser.DoesNotExist:
        pass

    return context
