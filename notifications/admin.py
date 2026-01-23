# admin.py
from django.contrib import admin
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.models import User
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'title', 'created_at']
    exclude = ("receiver",)

    def save_model(self, request, obj, form, change):
        obj.sender = request.user
        obj.save()

        # filter the role -default is teacher for sendinfg from admin to teacher
        teachers = User.objects.filter(userprofile__role="teacher")
        channel_layer = get_channel_layer()

        for teacher in teachers:
            # Create one notification per teacher
            Notification.objects.create(
                sender=request.user,
                receiver=teacher,
                title=obj.title,
                message=obj.message,
            )

            # Real-time send data
            async_to_sync(channel_layer.group_send)(
                f"user_{teacher.id}",
                {
                    "type": "send_notification",
                    "title": obj.title,
                    "message": obj.message,
                }
            )
