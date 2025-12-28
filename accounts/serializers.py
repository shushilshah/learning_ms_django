from django.contrib.auth.models import User
from rest_framework import serializers
from courses.models import UserProfile, Course, Enrollment, Lesson, Module, LessonProgress
from django.contrib.auth import authenticate

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password = validated_data['password']
        )

        # UserProfile.objects.create(user=user, role="student")   <----- this line of code giving me UNIQUE constraint error while signup.
        return user
    

class LoginSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        if not username or not password:
            raise serializers.ValidationError("Both username and password are required")
        
        user = authenticate(username=username, password=password)
        if user is None:
            raise serializers.ValidationError("Invalid credentials")
        
        if not user.is_active:
            raise serializers.ValidationError("User accoutn is disabled.")
        
        attrs['user'] = user
        return attrs
    

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'teacher', 'price', 'is_published', 'created_at', 'updated_at']


class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ['id', 'user', 'course', 'enrolled_at', 'valid_until', 'enrollment_type', 'is_active']
        read_only_fields = ['user', 'enrolled_at']


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ['id', 'course', 'title', 'is_published']

class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id','title', 'lesson_type', 'content', 'external_link', 'is_published', 'duration_minutes', 'attachments', 'created_at']
        read_only_fields = ['title', 'created_at']


class LessonProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonProgress
        fields = ['id', 'lesson', 'is_completed', 'started_at', 'completed_at', 'time_spent_minutes', 'last_accessed']
        read_only_fields = ['started_at', 'completed_at', 'last_accessed']


class CourseProgressSerilizer(serializers.Serializer):
    course_title = serializers.CharField()
    progress_percentage = serializers.FloatField()
    total_lessons = serializers.IntegerField()
    completed_lessons = serializers.IntegerField()


class RecentActivitySerializer(serializers.ModelSerializer):

    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    module_title = serializers.CharField(source='lesson.module.title', read_only=True)
    course_title = serializers.CharField(source='lesson.module.course.title', read_only=True)

    class Meta:
        model = LessonProgress
        fields = ['lesson_title', 'module_title', 'course_title', 'is_completed', 'last_accessed']


class TeacherDashboardSerializer(serializers.Serializer):
    course_title = serializers.CharField()
    total_students = serializers.IntegerField()
