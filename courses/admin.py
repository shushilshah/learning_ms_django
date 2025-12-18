from django.contrib import admin
from .models import *
# Register your models here.


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", 'role')
    list_filter = ('role',)
    search_fields = ("user__username",)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'teacher',
                    'price', 'is_published', 'created_at']
    list_filter = ['is_published', 'created_at']
    search_fields = ['title', 'description']
    inlines = [ModuleInline]


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'is_published']
    list_filter = ['course', 'is_published']
    inlines = [LessonInline]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'course',
                    'enrolled_at', 'valid_until', 'is_active']
    list_filter = ['is_active', 'enrollment_type']


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'module', 'lesson_type', 'order', 'is_published']
    list_filter = ['lesson_type', 'is_published', 'module__course']


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'module',
                    'passing_score', 'is_published']
    list_filter = ['is_published']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'quiz', 'question_type', 'points']
    inlines = [ChoiceInline]


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'lesson', 'is_completed', 'last_accessed']
    list_filter = ['is_completed']


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'quiz', 'score', 'is_passed', 'started_at']
    list_filter = ['is_passed']


admin.site.register(Notes)
