from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from .models import Notification
from django.contrib.auth.decorators import login_required
from courses.decorators import role_required
from courses.models import Enrollment
from django.db.models import Max
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

User = get_user_model()

@login_required
def notice_redirect(request):
    user = request.user
    profile = getattr(user, 'userprofile', None)
    role = profile.role.lower()
    if role == "teacher":
        return redirect("teacher_notice_list")
    elif role == "student":
        return redirect("student_notifications")
    else:
        return redirect("admin_publish_notice")



@login_required
# @role_required(['admin'])
def admin_publish_notice(request):
    print("🔥 admin_publish_notice view called")
    if request.method == 'POST':
        print("📨 POST request received")
        title = request.POST.get('title', "").strip()
        message = request.POST.get('message', "").strip()

        teachers = User.objects.filter(userprofile__role='teacher')
        channel_layer = get_channel_layer()

        for teacher in teachers:
            print("Sending to group:", f"user_{teacher.id}")
            Notification.objects.create(sender=request.user, receiver=teacher, title=title, message=message)
            
            async_to_sync(channel_layer.group_send)(
                f"user_{teacher.id}",
                {
                    "type": "send_notification",
                    "sender_role": "Admin",
                    "title": title,
                    "message": message,
                }
            )
        
        return redirect("admin_publish_notice")
    return render(request, "notifications/admin_publish_notice.html")


@login_required
@role_required(['teacher'])
def teacher_publish_notice(request):
    if request.method == 'POST':
        title = request.POST['title']
        message = request.POST['message']

        enrollments = Enrollment.objects.filter(course__teacher=request.user)
        students = User.objects.filter(
            id__in=enrollments.values_list('user_id', flat=True))
        channel_layer = get_channel_layer()


        for student in students:
            Notification.objects.create(
                sender=request.user,
                receiver = student,
                title=title,
                message=message
            )

            async_to_sync(channel_layer.group_send)(
                f"user_{student.id}",
                {
                    "type": "send_notification",
                    "sender_role": "teacher",
                    "title": title,
                    "message": message,
                }
            )
        return redirect("teacher_notice_list")
    return render(request, "notifications/teacher_publish.html")


@login_required
def notifications_list(request):
    notifications = request.user.notifications.order_by('-created_at')
    return render(request, 'notifications/list.html', {'notifications': notifications})


@login_required
def mark_notification_read(request, pk):
    notification = Notification.objects.get(id=pk, receiver=request.user)
    notification.is_read = True
    notification.save()
    return redirect("notifications_list")


@login_required
@role_required(['teacher'])
def teacher_notice_list(request):
    notices_by_teacher = (
        Notification.objects
        .filter(sender=request.user)
        .values('title', 'message')  # group by these fields
        .annotate(latest_created_at=Max('created_at'))
        .order_by('-latest_created_at')
    )
    
    notices_by_admin = Notification.objects.filter(
        receiver = request.user,
        sender__is_superuser=True,
    ).order_by('-created_at')

    context = {
        "notices_sent_to_student": notices_by_teacher,
        "notices_sent_by_admin": notices_by_admin
    }
    return render(request, 'notifications/teacher_notice_list.html', context)


@login_required
@role_required(['student'])
def student_notifications(request):
    notifications = Notification.objects.filter(receiver=request.user).order_by("-created_at")
    return render(request, "notifications/student_notifications.html", {"notifications": notifications})




