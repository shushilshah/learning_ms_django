# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    ROLE_CHOICES = (
        ("admin", 'Admin'),
        ("teacher", 'Teacher'),
        ('student', 'Student')
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=255, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='courses_taught')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_published = models.BooleanField(default=False)
    prerequistes = models.ManyToManyField(
        'self', symmetrical=False, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Module(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(models.Model):
    LESSON_TYPES = (
        ('video', 'Video'),
        ('text', 'Text'),
        ('html', "HTML Text"),
        ('pdf', "PDF/Document"),
        ('link', 'External Link'),
    )

    module = models.ForeignKey(
        Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPES)
    content = models.TextField(blank=True)
    video_url = models.FileField(blank=True)
    external_link = models.URLField(blank=True)
    transcripts = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    duration_minutes = models.PositiveIntegerField(default=0)
    attachments = models.FileField(upload_to="lesson_downloads/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.module.title} - {self.title}"


class Enrollment(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="enrollments")
    enrolled_at = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    enrollment_type = models.CharField(max_length=20, choices=[(
        'manual', 'Manual'), ('auto', "Automatic",)], default='manual')
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['user', 'course']

    def is_valid(self):
        if not self.is_active:
            return False
        if self.valid_until and timezone.now() > self.valid_until:
            return False
        return True


class LessonProgress(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name='progress')
    is_completed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent_minutes = models.PositiveIntegerField(default=0)
    last_accessed = models.DateTimeField(auto_now=True)

    # resume to continue functions
    resume_time = models.PositiveIntegerField(default=0)  # for video contnnt
    last_read_position = models.PositiveIntegerField(
        default=0)  # for text content

    class Meta:
        unique_together = ['user', 'lesson']


class Notes(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Quiz(models.Model):
    title = models.CharField(max_length=200)
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='quizzes', null=True, blank=True)
    module = models.ForeignKey(
        Module, on_delete=models.CASCADE, related_name='quizzes', null=True, blank=True)
    description = models.TextField(blank=True)
    time_limit_minutes = models.PositiveIntegerField(null=True, blank=True)
    passing_score = models.PositiveIntegerField(default=50)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    QUESTION_TYPES = (
        ('mcq', 'Multiple Choice'),
        ('true_false', 'True/False'),
    )
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    order = models.PositiveIntegerField(default=0)
    points = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.quiz.title} - {self.order}"


class Choice(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='choices')
    choice_text = models.CharField(max_length=400)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']


class QuizAttempt(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name='attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    is_passed = models.BooleanField(default=False)


class QuestionResponse(models.Model):
    attempt = models.ForeignKey(
        QuizAttempt, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choices = models.ManyToManyField(Choice, blank=True)
    is_correct = models.BooleanField(default=False)

    def evaluate_response(self):
        if self.question.question_type == 'true_false':
            selected_choice = self.selected_choices.first()
            if selected_choice:
                self.is_correct = selected_choice.is_correct
        else:
            correct_choices = set(self.question.choices.filter(
                is_correct=True).values_list('id', flat=True))
            selected_choices = set(
                self.selected_choices.values_list('id', flat=True))
            self.is_correct = correct_choices == selected_choices
        self.save()
