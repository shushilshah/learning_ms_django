from django.contrib import admin
from .models import Notification
from django.contrib.auth import get_user_model
from lms_system.forms import AdminNotificationForm
# Register your models here.


User = get_user_model()


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    form = AdminNotificationForm
    list_display = ['sender', 'receiver', 'title', 'created_at']


    def save_model(self, request, obj, form, change):
        # Sender is always the current admin
        sender = request.user

        # Send to all teachers
        teachers = User.objects.filter(userprofile__role="teacher")

        for teacher in teachers:
            Notification.objects.create(
                sender=sender,
                receiver=teacher,
                title=form.cleaned_data["title"],
                message=form.cleaned_data["message"]
            )
