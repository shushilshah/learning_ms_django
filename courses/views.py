from datetime import timedelta
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from .models import *
from django.utils import timezone
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib.auth import logout, login, authenticate
from .decorators import role_required
from lms_system.forms import *
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from rest_framework import status
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.db.models import Count

def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            # UserProfile.objects.create(user=user, role="student")
            login(request, user)
            return redirect("learning_dashboard")
    else:
        form = SignupForm()

    return render(request, "auth/signup.html", {"form": form})


def logout_user(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login_user')


def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username').strip()
        password = request.POST.get('password').strip()
        selected_role = request.POST['role']

        if not username or not password:
            return render(request, "auth/login.html", {"error": "Both username and password required."})

        if username != 'admin' and len(password) < 8:
            return render(request, "auth/login.html", {"error": "Password must be at least 8 characters."})
        
        if not User.objects.filter(username=username).exists():
            return render(request, 'auth/login.html', {"error": "Entered username does not exists."})

        if not User.objects.filter(username=username).exists():
            return render(request, "auth/login.html", {"error": "Username is case sensitive. Please enter the correct username."})
        


        user = authenticate(request, username=username, password=password)

        if user.userprofile.role != selected_role:
            return render(request, 'auth/login.html', {"error": f"You are not allowed to login as {selected_role.capitalize()}!"})


        if user is not None:    
            login(request, user)
            return redirect('role_redirect')
        else:
            return render(request, 'auth/login.html', {
                'error': 'Wrong password. Please try again.'
            })
    return render(request, 'auth/login.html')


@login_required
@role_required(['admin'])
def admin_dashboard(request):
    return render(request, 'admin/dashboard.html')


@login_required
@role_required(['teacher'])
def teacher_dashboard(request):
    return render(request, 'teacher/dashboard.html')


@login_required
@role_required(['student'])
def student_dashboard(request):
    return render(request, 'student/dashboard.html')


@login_required
def profile_view(request):
    return render(request, 'profile.html')


# @login_required
# def role_redirect(request):
    # role = request.user.userprofile.role

    # if role == 'admin':
    #     return redirect('/admin/')
    # elif role == 'teacher':
    #     return redirect('teacher_dashboard')
    # else:
    #     return redirect('learning_dashboard')

@login_required
def role_redirect(request):
    user = request.user

    if user.is_superuser:
        return redirect('/admin/')

    # If profile does not exist
    profile = getattr(user, "userprofile", None)
    if not profile:
        return redirect("learning_dashboard")

    role = profile.role

    if role == "teacher":
        return redirect("teacher_dashboard")

    elif role == "student":
        return redirect("learning_dashboard")

    else:
        # fallback if some unknown role
        return redirect("learning_dashboard")




@login_required
@role_required(['student'])
def student_dashboard(request):
    user = request.user

    enrollments = Enrollment.objects.filter(
        user=user, is_active=True
    ).select_related('course')

    courses_progress = []

    for enrollment in enrollments:
        course = enrollment.course
        modules = course.modules.all()

        module_data = []
        for module in modules:
            quizzes = module.quizzes.filter(is_published=True)

            for quiz in quizzes:
                quiz.can_start = ModuleProgress.objects.filter(
                    user=request.user,
                    module_id=module.id,
                    is_completed=True
                ).exists()

            module_data.append({
                'module': module,
                'quizzes': quizzes
            })


        total_lessons = Lesson.objects.filter(
            module__course=course, is_published=True
        ).count()

        completed_lessons = LessonProgress.objects.filter(
            user=user,
            lesson__module__course=course,
            is_completed=True
        ).count()

        progress_percentage = (
            (completed_lessons / total_lessons) * 100
            if total_lessons > 0 else 0
        )

        courses_progress.append({
            'course': course,
            'modules': module_data,
            'progress_percentage': int(progress_percentage),
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
        })

    recent_progress = LessonProgress.objects.filter(
        user=user
    ).select_related(
        'lesson',
        'lesson__module',
        'lesson__module__course'
    ).order_by('-last_accessed')[:5]

    context = {
        'courses_progress': courses_progress,
        'recent_progress': recent_progress,
        # "quizzes": quizzes
    }

    return render(request, 'student/dashboard.html', context)


@login_required
@role_required(['teacher'])
def teacher_dashboard(request):
    teacher = request.user

    courses = Course.objects.filter(teacher=teacher, is_published=True).annotate(
        total_modules= Count('modules', distinct=True),
        total_lessons = Count('modules__lessons', distinct=True),
        total_quizzes = Count('modules__quizzes', distinct=True)
    )

    approved_courses = Course.objects.filter(teacher=teacher, is_published=True)
    pending_courses = Course.objects.filter(teacher=teacher, is_published=False)

    course_data = []
    for course in courses:
        total_students = Enrollment.objects.filter(
            course=course, is_active=True).count()

        course_data.append({
            'course': course,
            'total_students': total_students,
        })

    context = {
        'course_data': course_data,
        'approved_courses': approved_courses,
        'pending_courses' : pending_courses,
    }

    return render(request, 'teacher/dashboard.html', context)


@login_required
@role_required(['teacher'])
def create_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user
            course.is_published = False
            course.save()
            messages.success(request, "Course submitted for admin aproval.")
            return redirect('teacher_dashboard')
    else:
        form = CourseForm()

    return render(request, 'teacher/create_course.html', {'form': form})


@login_required
@role_required(['teacher'])
def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if course.teacher != request.user:
        return HttpResponseForbidden("Not Allowed")

    if request.method == 'POST':
        form = EditCourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            return redirect("teacher_dashboard")

    else:
        form = EditCourseForm(instance=course)

    context = {
        'form': form,
        'course': course
    }

    return render(request, 'course/edit_course.html', context)


@login_required
@role_required(['teacher'])
def create_module(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if not course.is_published:
        raise PermissionDenied("Course not approved yet")

    if course.teacher != request.user:
        return HttpResponseForbidden("Not Allowed")

    if request.method == "POST":
        form = ModuleForm(request.POST)

        if form.is_valid():
            module = form.save(commit=False)
            module.course = course
            module.save()
            return redirect('teacher_course_detail', course_id=course.id)
    else:
        form = ModuleForm()

    context = {
        'form': form,
        'course': course
    }

    return render(request, 'teacher/create_module.html', context)


@login_required
@role_required(['teacher'])
def teacher_course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)

    if course.teacher != request.user:
        return HttpResponseForbidden("You are not allowed to view this course.")

    modules = course.modules.all()

    context = {
        'course': course,
        'modules': modules
    }
    return render(request, 'teacher/course_detail.html', context)



@login_required
@role_required(['teacher'])
def teacher_course_preview(request, course_id):
    course = get_object_or_404(Course, id=course_id, is_published=True)

    modules = course.modules.filter(is_published=True).prefetch_related('lessons')

    context = {
        'course': course,
        'modules': modules,
        'readonly': True
    }
    return render(request, 'teacher/course_preview.html', context)





@login_required
@role_required(['teacher'])
def create_lesson(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    course = module.course

    if not course.is_published:
        raise PermissionDenied("Course not approved yet")

    if course.teacher != request.user:
        return HttpResponseForbidden("Not Allowed")

    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.module = module
            lesson.save()
            return redirect('teacher_course_detail', course_id=course.id)

    else:
        form = LessonForm()

    context = {
        'form': form,
        'course': course,
        'module': module
    }
    return render(request, 'teacher/create_lesson.html', context)


def course_list(request):
    search = request.GET.get("q", "")
    courses = Course.objects.filter(is_published=True, title__icontains=search)
    

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
            'search': search
        }

    return render(request, 'course/course_list.html', context)


@login_required
def enroll_course(request, course_id):
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)

        # check if already enrolled
        if Enrollment.objects.filter(student=request.user, course=course).exists():
            messages.warning(
                request, f"You are already enrolled in {course.title}")

        else:
            Enrollment.objects.create(student=request.user, course=course)
            messages.success(
                request, f"You successfully enrolled in this {course.title} course.")

        return redirect("course_detail")
    return redirect('course_list')


def course_detail(request, course_id):
    course = Course.objects.get(id=course_id, is_published=True)

    # # Check if user is authenticated
    if not request.user.is_authenticated:
        return redirect('login')

    enrollment = None

    modules = course.modules.filter(
        is_published=True).prefetch_related('lessons').order_by('order')

    total_lessons = Lesson.objects.filter(
        module__course=course, is_published=True).count()
    completed__lessons = LessonProgress.objects.filter(
        user=request.user, lesson__module__course=course, is_completed=True).count()

    progress_percentage = (
        completed__lessons/total_lessons * 100) if total_lessons > 0 else 0

    has_started = LessonProgress.objects.filter(
        user=request.user, lesson__module__course = course
    ).exists() if request.user.is_authenticated else False

    context = {
        'course': course,
        'modules': modules,
        'progress_percentage': progress_percentage,
        'enrollment': enrollment,
        'has_started': has_started
    }
    return render(request, 'course/course_detail.html', context)



@login_required
def module_detail(request, module_id):
    module = Module.objects.get(id=module_id, is_published=True)
    lessons = module.lessons.filter(is_published=True)
    course = module.course
    modules = course.modules.filter(is_published=True)
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return redirect('login')  # Or show limited view

    enrollment = Enrollment.objects.filter(
        user=request.user, course=course, is_active=True
    ).first()


    # has_started = LessonProgress.objects.filter(
    #     user=request.user, lesson__module__course = course
    # ).exists() if request.user.is_authenticated else False

    context = {
        'module': module,
        'modules': modules,
        'course': course,
        'lessons': lessons,
        'enrollment': enrollment,
    }

    return render(request, 'course/module_detail.html', context)


@login_required
def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, is_published=True)
    course = lesson.module.course
    module = lesson.module

    # enrollment check
    enrollment = Enrollment.objects.filter(
        user=request.user,
        course=course,
        is_active=True
    ).first()

    # lesson progress
    if request.user.is_authenticated and request.user.userprofile.role == "student":
        progress, created = LessonProgress.objects.get_or_create(
        user=request.user,
        lesson=lesson
        )
        
        progress.started_at = timezone.now()
        progress.save()

    # next & previous lessons (same module)
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
        "module": module,
        'progress': progress,
        'next_lesson': next_lesson,
        'previous_lesson': previous_lesson,
        'enrollment': enrollment,
    }

    return render(request, 'course/lesson_detail.html', context)


@login_required
@role_required(['student'])
def resume_course(request, course_id):
    lessons = Lesson.objects.filter(module__course_id = course_id).order_by("module__order", "order")

    progress_qs = LessonProgress.objects.filter(user=request.user, lesson__in = lessons)

    incomplete = progress_qs.filter(is_completed=False).order_by("started_at").first()

    if incomplete:
        return redirect("lesson_detail", incomplete.lesson.id)
    
    last_accessed = progress_qs.order_by("-started_at").first()
    if last_accessed:
        return redirect("lesson_detail", last_accessed.lesson.id)

    first_lesson = lessons.first()
    if first_lesson:
        return redirect("lesson_detail", first_lesson.id)

    return redirect("course_detail", course_id)



@login_required
@role_required(['student'])
def mark_lesson_complete(request, lesson_id):
    if request.method == 'POST':
        lesson = Lesson.objects.get(id=lesson_id)
        progress, created = LessonProgress.objects.get_or_create(
            user=request.user, lesson=lesson)

        if not progress.is_completed:
            progress.is_completed = True
            progress.completed_at = timezone.now()
            progress.save()

        # check module complete or not

        module = lesson.module
        total_lessons = module.lessons.count()
        completed_lessons = LessonProgress.objects.filter(
            user=request.user,
            lesson__module=module,
            is_completed=True
        ).count()

        if total_lessons == completed_lessons:
            ModuleProgress.objects.update_or_create(
                user=request.user,
                module=module,
                defaults={
                    'is_completed': True,
                    'completed_at': timezone.now()
                }
            )

        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'error'}, status=status.HTTP_400_BAD_REQUEST)


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

    # if missing_prerequisities.exists():
    #     return render(request, 'course/prerequisites_missing.html', {
    #         'course': course,
    #         'missing_prerequisities': missing_prerequisities
    #     })

    enrollment, created = Enrollment.objects.get_or_create(
        user=request.user,
        course=course,
        defaults={'is_active': True}
    )

    if not created:
        enrollment.is_active = True
        enrollment.save()

    return redirect('course_detail', course_id=course_id)


# @login_required
# @role_required(['student'])
# def learning_dashboard(request):
#     user = request.user

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

@login_required
@role_required(['student'])
def learning_dashboard(request):
    user = request.user

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
            completed_lessons / total_lessons * 100) if total_lessons > 0 else 0

        # 🔹 Build module-level progress
        modules_data = []
        modules = Module.objects.filter(course=course)
        for module in modules:
            module_total = Lesson.objects.filter(
                module=module, is_published=True).count()
            module_completed = LessonProgress.objects.filter(
                user=request.user, lesson__module=module, lesson__is_published=True, is_completed=True).count()

            # Example: attach quizzes if you have them
            quizzes = Quiz.objects.filter(module=module)
            quizzes_data = []
            for quiz in quizzes:
                quizzes_data.append({
                    "title": quiz.title,
                    "id": quiz.id,
                    "can_start": module_completed == module_total and module_total > 0
                })

            modules_data.append({
                "module": module,
                "total_lessons": module_total,
                "completed_lessons": module_completed,
                "quizzes": quizzes_data,
            })

        course_progress.append({
            'course': course,
            'progress_percentage': progress_percentage,
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'enrollment': enrollment,
            'modules': modules_data,   # 🔹 Now template has real data
        })

    # recent activity
    recent_activities = LessonProgress.objects.filter(user=request.user).select_related(
        'lesson', 'lesson__module', 'lesson__module__course').order_by('-last_accessed')[:10]

    context = {
        'courses_progress': course_progress,
        'recent_progress': recent_activities,
    }
    return render(request, 'student/dashboard.html', context)





# admin see pending courses
@login_required
@role_required(['admin'])
def pending_courses(request):
    courses = Course.objects.filter(is_published=False)
    context = {
        'courses': courses
    }
    return redirect(request, 'course/pending_courses.html', context)


@login_required
@role_required(['admin'])
def approve_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    course.is_published = True
    course.updated_at = timezone.now()
    course.save()
    messages.success(request, "Course '{course.title}' approved.")
    return redirect('pending_course')



@login_required
@role_required(['student'])
def start_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, is_published=True)

    # check module complete or not
    module = quiz.module

    module_progress = ModuleProgress.objects.filter(
        user=request.user,
        module=module,
        is_completed=True
    ).exists()

    if not module_progress:
        messages.error(request, "You must complete this module before taking the quiz.")
        return redirect('student_dashboard')

    # prevent multiple active attempts
    attempt, created  = QuizAttempt.objects.get_or_create(
        user=request.user,
        quiz=quiz,
        completed_at__isnull = True
    )
    return redirect('take_quiz', quiz_id=quiz_id)


@login_required
@role_required(['student'])
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, is_published=True)

    # Get the active attempt for this user and quiz
    attempt = QuizAttempt.objects.filter(
        user=request.user,
        quiz=quiz,
        completed_at__isnull=True
    ).first()

    if not attempt:
        messages.error(request, "No active attempt found for this quiz.")
        return redirect('student_dashboard')

    questions = quiz.questions.prefetch_related("options")
    return render(request, "quizzes/take_quiz.html", {
        "attempt": attempt,
        "questions": questions,
        "duration_seconds": quiz.duration_minutes * 60,
        "started_at": attempt.started_at.timestamp(),
    })







@login_required
def submit_quiz(request, attempt_id):
    attempt = get_object_or_404(
        QuizAttempt,
        id=attempt_id,
        user=request.user,
        completed_at__isnull=True
    )

    # prevent re-submit
    if attempt.completed_at:
        return redirect('quiz_result', attempt_id=attempt.id)

    quiz_duration = timedelta(minutes=attempt.quiz.duration_minutes)
    time_elapsed = timezone.now() - attempt.started_at

    # Time Over ---> auto submit features

    if time_elapsed > quiz_duration:
        attempt.completed_at = timezone.now()
        attempt.score = 0
        attempt.is_passed = False
        attempt.save()
        return redirect('quiz_result', attempt_id=attempt.id)
    

    total_score = 0
    max_score = 0

    for question in attempt.quiz.questions.all():
        selected_option_id = request.POST.get(f"question_{question.id}")
        if not selected_option_id:
            continue

        selected_option = AnswerOption.objects.get(id=selected_option_id)

        response = QuestionResponse.objects.create(
            attempt=attempt,
            question=question,
            selected_option=selected_option
        )
        response.evaluate_response()

        max_score += question.points
        if response.is_correct:
            total_score += question.points

    attempt.score = total_score
    attempt.is_passed = total_score >= (max_score * 0.5)
    attempt.completed_at = timezone.now()
    attempt.save()

    return redirect("quiz_result", attempt_id=attempt.id)



@login_required
def quiz_result(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)

    responses = attempt.responses.select_related("question", "selected_option")

    return render(request, "quizzes/quiz_result.html", {
        "attempt": attempt,
        "responses": responses
    })



@login_required
def quiz_page(request, module_id):
    quizzes = Quiz.objects.filter(module_id=module_id, is_published=True)
    selected_quiz = None
    questions = None
    result = None

    quiz_id = request.GET.get("quiz")

    if quiz_id:
        selected_quiz = get_object_or_404(Quiz, id=quiz_id)

        if request.method == "POST":
            score = 0
            for q in selected_quiz.questions.all():
                selected = request.POST.get(str(q.id))
                if selected:
                    try:
                        choice = AnswerOption.objects.get(id=selected)
                        if choice.is_correct:
                            score += 1
                    except AnswerOption.DoesNotExist:
                        pass
                    score += 1

            percent = int((score / selected_quiz.questions.count()) * 100)

            QuizAttempt.objects.create(
                user=request.user,
                quiz=selected_quiz,
                score=percent,
                completed_at=timezone.now(),
                is_passed=(percent >= selected_quiz.passing_score),
            )

            result = {
                "score": percent,
                "passed": percent >= selected_quiz.passing_score
            }

        else:
            questions = selected_quiz.questions.prefetch_related("choices")

    return render(request, "quizzes/take_quiz.html", {
        "quizzes": quizzes,
        "selected_quiz": selected_quiz,
        "questions": questions,
        "result": result
    })


@login_required
@role_required(['teacher'])
def create_quiz(request, course_id):
    courses = get_object_or_404(Course, id=course_id)

    modules = courses.modules.all()
   
    if request.method == "POST":
        module_id = request.POST.get("module")
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        time_limit = request.POST.get("time_limit_minutes")
        pass_mark = request.POST.get("passing_score")

        errors = []
        if not module_id:
            errors.append("Module is required.")
        if not title:
            errors.append("Title is required.")

        try:
            time_limit_val = int(time_limit) if time_limit not in (None, "") else 0
        except (TypeError, ValueError):
            time_limit_val = 0
            errors.append("Time limit must be an integer.")

        try:
            pass_mark_val = int(pass_mark) if pass_mark not in (None, "") else 0
        except (TypeError, ValueError):
            pass_mark_val = 0
            errors.append("Passing score must be an integer.")

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, "quizzes/teacher_quiz_create.html", {
                "modules": modules,
                "data": request.POST,
            })

        quiz = Quiz.objects.create(
            module_id=module_id,
            title=title,
            description=description,
            time_limit_minutes=time_limit_val,
            passing_score=pass_mark_val,
            is_published=False,
        )

        return redirect("add_question", quiz.id)

    return render(request, "quizzes/teacher_quiz_create.html", {
        "courses": courses,
        "modules": modules
    })




@login_required
@role_required(['teacher'])
def add_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    if request.method == "POST":
        questions_dict = {}

        for key, value in request.POST.items():
            if key.startswith("questions"):
                parts = key.replace("questions[", "").replace("]", "").split("[")
                q_index = parts[0]
                field = parts[1]

                questions_dict.setdefault(q_index, {})[field] = value

        for _, q_data in questions_dict.items():
            with transaction.atomic():

                # 1️⃣ Create Question
                question = Question.objects.create(
                    quiz=quiz,
                    question_text=q_data.get("question"),
                    question_type="mcq",
                )

                # 2️⃣ Create Answer Options
                options = []
                for i in range(1, 5):
                    option = AnswerOption.objects.create(
                        question=question,
                        choice_text=q_data.get(f"option{i}"),
                        order=i,
                        is_correct = False
                    )
                    options.append(option)

                # 3️⃣ Create CorrectAnswer
                # correct_index = int(q_data.get("correct")) - 1
                correct_value = q_data.get("correct")

                option_map = {
                    "option1": 0,
                    "option2": 1,
                    "option3": 2,
                    "option4": 3,
                }

                if correct_value not in option_map:
                    raise ValueError(f"Invalid correct option: {correct_value}")
                
                correct_index = option_map[correct_value]
                correct_option = options[correct_index]
                correct_option.is_correct = True
                correct_option.save()


                # CorrectAnswer.objects.create(
                #     question=question,
                #     answer_option=correct_option
                # )

        if "publish" in request.POST:
            quiz.is_published = True
            quiz.save()
            messages.success(request, "Quiz published successfully!")
            return redirect("teacher_dashboard")

        messages.success(request, "Questions added successfully!")
        # return redirect("add_question", quiz_id=quiz.id)
        return redirect("Thank you")

    return render(request, "quizzes/teacher_add_question.html", {"quiz": quiz})
