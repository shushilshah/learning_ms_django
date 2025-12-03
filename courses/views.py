# from django.shortcuts import render, redirect
# from django.contrib.auth.decorators import login_required
# from courses.models import Course, Enrollment, Lesson, LessonProgress, Module
# from django.utils import timezone


# # @login_required
# def course_list(request):
#     courses = Course.objects.filter(is_published=True)
#     user_enrollments = Enrollment.objects.filter(
#         user=request.user, is_active=True)

#     for enrollment in user_enrollments:
#         if not enrollment.is_valid():
#             enrollment.is_active = False
#             enrollment.save()

#     enrolled_course_ids = user_enrollments.filter(
#         is_active=True).values_list('course_id', flat=True)

#     context = {
#         'courses': courses,
#         'enrolled_course_ids': list(enrolled_course_ids),
#     }

#     return render(request, 'course/course_list.html', {'courses': courses})


# # @login_required
# def course_detail(request, course_id):
#     course = Course.objects.get(id=course_id, is_published=True)
#     enrollment = Enrollment.objects.filter(
#         user=request.user, course=course, is_active=True).first()

#     if not enrollment or not enrollment.is_valid():
#         return redirect('course_list')

#     modules = course.modules.filter(
#         is_published=True).prefetch_related('lessons').order_by('order')

#     total_lessons = Lesson.objects.filter(
#         module__course=course, is_published=True).count()
#     completed__lessons = LessonProgress.objects.filter(
#         user=request.user, lesson__module__course=course, is_completed=True).count()

#     progress_percentage = (
#         completed__lessons/total_lessons * 100) if total_lessons > 0 else 0

#     context = {
#         'course': course,
#         'modules': modules,
#         'progress_percentage': progress_percentage,
#         'enrollment': enrollment,
#     }
#     return render(request, 'course/course_detail.html', context)


# # @login_required
# def module_detail(request, module_id):
#     module = Module.objects.get(id=module_id, is_published=True)
#     lessons = module.lessons.filter(is_published=True)
#     course = module.course

#     enrollment = Enrollment.objects.filter(
#         user=request.user, course=course, is_active=True
#     ).first()

#     context = {
#         'module': module,
#         'course': course,
#         'lessons': lessons,
#         'enrollment': enrollment
#     }

#     return render(request, 'course/module_detail.html', context)


# # @login_required
# def lesson_detail(request, lesson_id):
#     lesson = Lesson.objects.get(id=lesson_id, is_published=True)
#     course = lesson.module.course
#     enrollment = Enrollment.objects.get(
#         user=request.user, course=lesson.module.course, is_active=True)

#     if not enrollment.is_valid():
#         return redirect('course_list')

#     # update the lesson progress of user
#     progress, created = LessonProgress.objects.get_or_create(
#         user=request.user, lesson=lesson)
#     progress.last_accessed = timezone.now()
#     # save the progress
#     progress.save()

#     # get next and previuos lessons
#     next_lesson = Lesson.objects.filter(
#         module=lesson.module,
#         order__gt=lesson.order,
#         is_published=True
#     ).order_by('order').first()

#     previous_lesson = Lesson.objects.filter(
#         module=lesson.module,
#         order__lt=lesson.order,
#         is_published=True
#     ).order_by('-order').first()

#     context = {
#         'lesson': lesson,
#         'course': course,
#         'progress': progress,
#         'next_lesson': next_lesson,
#         'previous_lesson': previous_lesson,
#         'enrollment': enrollment
#     }

#     return render(request, 'course/lesson_detail.html', context)


# # @login_required
# def enroll_course(request, course_id):
#     course = Course.objects.get(id=course_id, is_published=True)
#     prerequisties = course.prerequistes.all()
#     user_completed_courses = Course.objects.filter(enrollments__user=request.user, enrollments__is_active=True,
#                                                    modules__lessons__progress__user=request.user, modules__lessons__progress__is_completed=True).distinct()

#     missing_prerequisties = prerequisties.exclude(
#         id__in=user_completed_courses)

#     if missing_prerequisties.exists():
#         return render(request, 'course/prerequisites_missing.html', {
#             'course': course,
#             'missing_prerequisties': missing_prerequisties
#         })

#     enrollment, created = Enrollment.objects.get_or_create(
#         user=request.user,
#         course=course,
#         defaults={'is_active': True}
#     )

#     if not created:
#         enrollment.is_active = True
#         enrollment.save()

#     return redirect('course_detail', course_id=course_id)


# # @login_required
# def learning_dashboard(request):
#     user_enrollments = Enrollment.objects.filter(
#         user=request.user, is_active=True).select_related('course')

#     course_progress = []
#     for enrollment in user_enrollments:
#         course = enrollment.course
#         total_lessons = Lesson.objects.filter(
#             module__course=course, is_published=True).count()
#         completed_lessons = LessonProgress.objects.filter(
#             user=request.user, lesson__module__course=course, is_completed=True).count()
#         progress_percentage = (
#             completed_lessons/total_lessons * 100) if total_lessons > 0 else 0

#         course_progress.append({
#             'course': course,
#             'progress_percentage': progress_percentage,
#             'total_lessons': total_lessons,
#             'completed_lessons': completed_lessons,
#             'enrollment': enrollment,

#         })

#     # recent activity
#     recent_activities = LessonProgress.objects.filter(user=request.user).select_related(
#         'lesson', 'lesson__module', 'lesson__module__course').order_by('-last_accessed')[:10]

#     context = {
#         'courses_progress': course_progress,
#         'recent_progress': recent_activities,
#     }
#     return render(request, 'dashboard.html', context)


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from courses.models import Course, Enrollment, Lesson, LessonProgress, Module, Quiz, QuizAttempt
from django.utils import timezone
from django.http import JsonResponse


def course_list(request):
    courses = Course.objects.filter(is_published=True)

    # Check if user is authenticated before querying enrollments
    if request.user.is_authenticated:
        user_enrollments = Enrollment.objects.filter(
            user=request.user, is_active=True)

        for enrollment in user_enrollments:
            if not enrollment.is_valid():
                enrollment.is_active = False
                enrollment.save()

        enrolled_course_ids = user_enrollments.filter(
            is_active=True).values_list('course_id', flat=True)

        context = {
            'courses': courses,
            'enrolled_course_ids': list(enrolled_course_ids),
        }
    else:
        context = {
            'courses': courses,
            'enrolled_course_ids': [],
        }

    return render(request, 'course/course_list.html', context)


def course_detail(request, course_id):
    course = Course.objects.get(id=course_id, is_published=True)

    # Check if user is authenticated
    if not request.user.is_authenticated:
        # Redirect to login or show limited view
        return redirect('login')  # Or render a public preview page

    enrollment = Enrollment.objects.filter(
        user=request.user, course=course, is_active=True).first()

    if not enrollment or not enrollment.is_valid():
        return redirect('course_list')

    modules = course.modules.filter(
        is_published=True).prefetch_related('lessons').order_by('order')

    total_lessons = Lesson.objects.filter(
        module__course=course, is_published=True).count()
    completed__lessons = LessonProgress.objects.filter(
        user=request.user, lesson__module__course=course, is_completed=True).count()

    progress_percentage = (
        completed__lessons/total_lessons * 100) if total_lessons > 0 else 0

    context = {
        'course': course,
        'modules': modules,
        'progress_percentage': progress_percentage,
        'enrollment': enrollment,
    }
    return render(request, 'course/course_detail.html', context)


def module_detail(request, module_id):
    module = Module.objects.get(id=module_id, is_published=True)
    lessons = module.lessons.filter(is_published=True)
    course = module.course

    # Check if user is authenticated
    if not request.user.is_authenticated:
        return redirect('login')  # Or show limited view

    enrollment = Enrollment.objects.filter(
        user=request.user, course=course, is_active=True
    ).first()

    context = {
        'module': module,
        'course': course,
        'lessons': lessons,
        'enrollment': enrollment
    }

    return render(request, 'course/module_detail.html', context)


def lesson_detail(request, lesson_id):
    lesson = Lesson.objects.get(id=lesson_id, is_published=True)
    course = lesson.module.course

    # Check if user is authenticated
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        enrollment = Enrollment.objects.get(
            user=request.user, course=lesson.module.course, is_active=True)
    except Enrollment.DoesNotExist:
        return redirect('course_list')

    if not enrollment.is_valid():
        return redirect('course_list')

    # update the lesson progress of user
    progress, created = LessonProgress.objects.get_or_create(
        user=request.user, lesson=lesson)
    progress.last_accessed = timezone.now()
    # save the progress
    progress.save()

    # get next and previous lessons
    next_lesson = Lesson.objects.filter(
        module=lesson.module,
        order__gt=lesson.order,
        is_published=True
    ).order_by('order').first()

    previous_lesson = Lesson.objects.filter(
        module=lesson.module,
        order__lt=lesson.order,
        is_published=True
    ).order_by('-order').first()

    context = {
        'lesson': lesson,
        'course': course,
        'progress': progress,
        'next_lesson': next_lesson,
        'previous_lesson': previous_lesson,
        'enrollment': enrollment
    }

    return render(request, 'course/lesson_detail.html', context)


def mark_lesson_complete(request, lesson_id):
    if request.method == 'POST':
        lesson = Lesson.objects.get(id=lesson_id)
        progress, created = LessonProgress.objects.get_or_create(
            user=request.user, lesson=lesson)

        if not progress.is_completed:
            progress.is_completed = True
            progress.completed_at = timezone.now()
            progress.save()

        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'error'})


@login_required
def update_time_spent(request, lesson_id):
    if request.method == 'POST':
        lesson = Lesson.objects.get(id=lesson_id)
        time_spent = request.POST.get('time_spent', 0)

        try:
            progress, created = LessonProgress.objects.get_or_create(
                user=request.user, lesson=lesson)
            progress.time_spent_minutes += int(time_spent)
            progress.save()

            return JsonResponse({'status': 'success'})
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid time value'})

    return JsonResponse({'status': 'error'})


@login_required
def take_quiz(request, quiz_id):
    quiz = Quiz.objects.get(id=quiz_id, is_published=True)

    # if user is enrolled in course or not
    if quiz.course:
        enrollment = Enrollment.objects.get(
            user=request.user, course=quiz.course, is_active=True)
        if not enrollment.is_valid():
            return redirect('course_list')

    # check for exsting active attempt
    active_attempt = QuizAttempt.objects.filter(
        user=request.user, quiz=quiz, completed_at__isnull=True).first()

    if not active_attempt:
        active_attempt = QuizAttempt.objects.create(
            user=request.user, quiz=quiz)

    questions = quiz.questions.all().prefetch_related('choices')

    context = {
        'quiz': quiz,
        'questions': questions,
        'attempt': active_attempt,
    }
    return render(request, 'quizzes/take_quiz.html', context)


def enroll_course(request, course_id):
    course = Course.objects.get(id=course_id, is_published=True)

    # Check if user is authenticated
    if not request.user.is_authenticated:
        return redirect('login')

    prerequisities = course.prerequistes.all()
    user_completed_courses = Course.objects.filter(enrollments__user=request.user, enrollments__is_active=True,
                                                   modules__lessons__progress__user=request.user, modules__lessons__progress__is_completed=True).distinct()

    missing_prerequisities = prerequisities.exclude(
        id__in=user_completed_courses)

    if missing_prerequisities.exists():
        return render(request, 'course/prerequisites_missing.html', {
            'course': course,
            'missing_prerequisities': missing_prerequisities
        })

    enrollment, created = Enrollment.objects.get_or_create(
        user=request.user,
        course=course,
        defaults={'is_active': True}
    )

    if not created:
        enrollment.is_active = True
        enrollment.save()

    return redirect('course_detail', course_id=course_id)


@login_required
def learning_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')

    user_enrollments = Enrollment.objects.filter(
        user=request.user, is_active=True).select_related('course')

    course_progress = []
    for enrollment in user_enrollments:
        course = enrollment.course
        total_lessons = Lesson.objects.filter(
            module__course=course, is_published=True).count()
        completed_lessons = LessonProgress.objects.filter(
            user=request.user, lesson__module__course=course, is_completed=True).count()
        progress_percentage = (
            completed_lessons/total_lessons * 100) if total_lessons > 0 else 0

        course_progress.append({
            'course': course,
            'progress_percentage': progress_percentage,
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'enrollment': enrollment,
        })

    # recent activity
    recent_activities = LessonProgress.objects.filter(user=request.user).select_related(
        'lesson', 'lesson__module', 'lesson__module__course').order_by('-last_accessed')[:10]

    context = {
        'courses_progress': course_progress,
        'recent_progress': recent_activities,
    }
    return render(request, 'dashboard.html', context)
