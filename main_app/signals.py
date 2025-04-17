# timesheet/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Timesheet,Admin,Manager,Employee,CustomUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import Timesheet

@receiver(post_save, sender=Timesheet)
def calculate_work_hours(sender, instance, created, **kwargs):
    if not created:
        return

    user = instance.custom_user
    now = instance.clocking_time
    current_log = instance.logging

    # Get the previous timesheet entry before this one
    previous_entry = Timesheet.objects.filter(
        custom_user=user,
        clocking_time__lt=now
    ).exclude(id=instance.id).order_by('-clocking_time').first()

    if not previous_entry:
        return

    def get_duration(later, earlier):
        return later - earlier  # returns timedelta

    if previous_entry.logging == "IN" and current_log == "OUT":
        work_duration = get_duration(now, previous_entry.clocking_time)
        instance.clocked_hours = work_duration
        instance.total_payroll_hours = work_duration
        instance.save(update_fields=["clocked_hours", "total_payroll_hours"])

    elif previous_entry.logging == "BREAK_IN" and current_log == "BREAK_OUT":
        break_duration = get_duration(now, previous_entry.clocking_time)
        instance.break_hours = break_duration
        instance.save(update_fields=["break_hours"])

    elif current_log == "OUT":
        last_in = Timesheet.objects.filter(
            custom_user=user,
            logging="IN",
            clocking_time__lt=now
        ).order_by('-clocking_time').first()

        if not last_in:
            return

        total_work_duration = get_duration(now, last_in.clocking_time)

        # Match BREAK_IN and BREAK_OUT pairs
        break_ins = Timesheet.objects.filter(
            custom_user=user,
            logging="BREAK_IN",
            clocking_time__gt=last_in.clocking_time,
            clocking_time__lt=now
        ).order_by('clocking_time')

        total_break_duration = timedelta()

        for break_in in break_ins:
            break_out = Timesheet.objects.filter(
                custom_user=user,
                logging="BREAK_OUT",
                clocking_time__gt=break_in.clocking_time,
                clocking_time__lt=now
            ).order_by('clocking_time').first()

            if break_out:
                total_break_duration += get_duration(break_out.clocking_time, break_in.clocking_time)

        total_payroll = total_work_duration - total_break_duration
        if total_payroll.total_seconds() < 0:
            total_payroll = timedelta()  # Prevent negative payroll

        instance.clocked_hours = total_work_duration
        instance.break_hours = total_break_duration
        instance.total_payroll_hours = total_payroll
        instance.save(update_fields=["clocked_hours", "break_hours", "total_payroll_hours"])

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == 1:
            Admin.objects.create(admin=instance)
        if instance.user_type == 2:
            Manager.objects.create(admin=instance)
        if instance.user_type == 3:
            Employee.objects.create(admin=instance)


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    if instance.user_type == 1:
        instance.admin.save()
    if instance.user_type == 2:
        instance.manager.save()
    if instance.user_type == 3:
        instance.employee.save()


