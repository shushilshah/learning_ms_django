from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from courses.models import Course, Enrollment, Lesson, LessonProgress, Module, Quiz, QuizAttempt, Choice, QuestionResponse, UserProfile
from django.utils import timezone
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib.auth import logout, login, authenticate
from .decorators import role_required
from lms_system.forms import CourseForm, LessonForm, ModuleForm, SignupForm
from django.contrib import messages


def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user, role="student")
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
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('role_redirect')
        else:
            return render(request, 'auth/login.html', {
                'error': 'Invalid Credentials'
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
def role_redirect(request):
    role = request.user.userprofile.role

    if role == 'admin':
        return redirect('/admin/')
    elif role == 'teacher':
        return redirect('teacher_dashboard')
    else:
        return redirect('student_dashboard')


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
    }

    return render(request, 'student/dashboard.html', context)


@login_required
@role_required(['teacher'])
def teacher_dashboard(request):
    teacher = request.user

    courses = Course.objects.filter(teacher=teacher)
    course_data = []
    for course in courses:
        total_students = Enrollment.objects.filter(
            course=course, is_active=True).count

        course_data.append({
            'course': course,
            'total_students': total_students,
        })

    context = {
        'course_data': course_data
    }

    return render(request, 'teacher/dashboard.html', context)


@login_required
@role_required(['teacher'])
def create_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user
            course.save()
            return redirect('teacher_dashboard')
    else:
        form = CourseForm()

    return render(request, 'teacher/create_course.html', {'form': form})


@login_required
@role_required(['teacher'])
def create_module(request, course_id):
    course = get_object_or_404(Course, id=course_id)

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
    modules = course.modules.all()

    context = {
        'course': course,
        'modules': modules
    }
    return render(request, 'teacher/course_detail.html', context)


@login_required
@role_required(['teacher'])
def create_lesson(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    course = module.course

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
    modules = course.modules.filter(is_published=True)
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return redirect('login')  # Or show limited view

    enrollment = Enrollment.objects.filter(
        user=request.user, course=course, is_active=True
    ).first()

    context = {
        'module': module,
        'modules': modules,
        'course': course,
        'lessons': lessons,
        'enrollment': enrollment
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
    progress, created = LessonProgress.objects.get_or_create(
        user=request.user,
        lesson=lesson
    )
    progress.last_accessed = timezone.now()
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


@login_required
def submit_quiz(request, attempt_id):
    attempt = QuizAttempt.objects.get(id=attempt_id, user=request.user)

    if request.method == 'POST':
        total_questions = attempt.quiz.questions.count()
        correct_answers = 0

        for question in attempt.quiz.questions.all():
            selected_choice_id = request.POST.getlist(
                f'quesiton_{question.id}')

            response = QuestionResponse.objects.create(
                attempt=attempt, question=question)

            if selected_choice_id:
                selected_choices = Choice.objects.filter(
                    id__in=selected_choice_id)

                response.selected_choices.set(selected_choices)

            response.evaluate_response()

            if response.is_correct:
                correct_answers += 1

        score = (correct_answers / total_questions) * \
            100 if total_questions > 0 else 0
        attempt.score = score
        attempt.is_passed = score >= attempt.quiz.passing_score
        attempt.save()

        return redirect('quiz_result', attempt_id=attempt.id)

    return redirect('take_quiz', quiz_id=attempt.quiz.id)


@login_required
def quiz_result(request, attempt_id):
    attempt = QuizAttempt.objects.get(id=attempt_id, user=request.user)
    context = {
        'attempt': attempt,
        'responses': attempt.responses.all().select_related('question'),
    }
    return render(request, 'quizzes/quiz_result.html', context)


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
