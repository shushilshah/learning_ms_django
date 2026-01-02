from rest_framework import status, views, generics
from rest_framework.response import Response
from .serializers import *
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from courses.models import *
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from django.utils import timezone


###################################### Creadentials Section #############################################

class SignupAPIView(views.APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "Signup successfull",
                "user": {
                    "username": user.username,
                    "email": user.email,
                    "role": user.userprofile.role
                }
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class LoginAPIView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username= request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)

        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "Login Successful",
                "user": {
                    "username": user.username,
                    "role": getattr(user.userprofile, "role", None)                
                    },
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        

class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({
                "detail": "Successfully logged out."
            }, status=status.HTTP_205_RESET_CONTENT)
        
        except Exception as e:
            return Response({
                "detail": "Invalid token"
            }, status=status.HTTP_400_BAD_REQUEST)




###################################### Landing pages section #####################################


class CourseListAPIView(generics.ListAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Course.objects.filter(is_published=True)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        enrolled_course_ids =[]
        if request.user.is_authenticated:
            user_enrollments = Enrollment.objects.filter(user=request.user, is_active=True)

            # deactivate expired enrollments

            for enrollment in user_enrollments:
                if not enrollment.is_valid():
                    enrollment.is_active = False
                    enrollment.save()
            enrolled_course_ids = list(user_enrollments.filter(is_active=True).values_list('course_id',flat=True))

        return Response({
            "courses": serializer.data,
            "enrolled_courses_ids": enrolled_course_ids
        }, status=status.HTTP_200_OK)


class EnrollCourseAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)

        # check if already enrolled

        if Enrollment.objects.filter(user=request.user, course=course).exists():
            return Response({"messages": f"You are already enrolled in this {course.title} course."}, status=status.HTTP_400_BAD_REQUEST)
        
        enrollment = Enrollment.objects.create(user=request.user, course=course)
        return Response(
            {
                "message": f"You successfully enrolled in {course.title} course",
                "enrollment_id": enrollment.id,
                "course_id": course.id
            }, status=status.HTTP_201_CREATED
        )
    

class LessonDetailAPIView(generics.ListAPIView):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, lesson_id):
        lesson = get_object_or_404(Lesson, id=lesson_id, is_published=True)
        module = lesson.module
        course = module.course

        #check enrollment
        enrollment = Enrollment.objects.filter(user=request.user, course=course, is_active=True).first()

        progress_data = None
        if request.user.userprofile.role == "student":
            progress, _ = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)

            progress.started_at = timezone.now()
            progress.save()
            progress_data = {
                "started_at": progress.started_at,
                "completed_at": progress.completed_at
            }

        next_lesson = Lesson.objects.filter(
            module=module,
            order__gt = lesson.order,
            is_published=True
        ).order_by('order').first()

        previous_lesson = Lesson.objects.filter(
            module=module,
            order__lt= lesson.order,
            is_published = True
        ).order_by('-order').first()


        return Response({
            'lesson': LessonSerializer(lesson).data,
            'module': ModuleSerializer(module).data,
            'course': CourseSerializer(course).data,
            "enrollment": bool(enrollment),
            "progress": progress_data,
            "next_lesson": LessonSerializer(next_lesson).data if next_lesson else None,
            'previous_lesson': LessonSerializer(previous_lesson).data if previous_lesson else None
        })


class ModuleDetailAPIView(generics.ListAPIView):
    serializer = ModuleSerializer

    def get(self, request, module_id):
        module = get_object_or_404(Module, id=module_id, is_published=True)
        course = module.course

        # check enrollment
        enrollment = Enrollment.objects.filter(user=request.user, course=course, is_active=True).first()

        return Response({
            "module": module.title,
            "course": course.title,
            "enrollment": bool(enrollment),
        }, status=status.HTTP_200_OK)
    

class LessonProgressAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, lesson_id):
        lesson = get_object_or_404(Lesson, id=lesson_id, is_published=True)
        progress, _ = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
        serializer = LessonProgressSerializer(progress)
        return Response(serializer.data)

    def put(self, request, lesson_id):
        lesson = get_object_or_404(Lesson,id=lesson_id, is_published=True)
        progress, _ = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)

        serializer = LessonProgressSerializer(progress, data=request.data, partial=True)
        if serializer.is_valid():
            updated_progress = serializer.save()
            if updated_progress.is_completed and not updated_progress.completed_at:
                updated_progress.completed_at = timezone.now()
                updated_progress.save()

            return Response(LessonProgressSerializer(updated_progress).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class LearningDashboardAPIView(APIView):
    permisson_classes = [IsAuthenticated]

    def get(self, request):
        enrollments = Enrollment.objects.filter(user=request.user, is_active=True).select_related("course")

        course_progress_data = []

        for enrollment in enrollments:
            course = enrollment.course
            total_lessons = Lesson.objects.filter(module__course=course, is_published=True).count()
            completed_lessons = LessonProgress.objects.filter(
                user=request.user, lesson__module__course=course, is_completed=True
            ).count()

            progress_percentage = (completed_lessons/total_lessons * 100) if total_lessons > 0 else 0

            course_progress_data.append({
                "course_title": course.title,
                "progress_percentage": progress_percentage,
                "total_lessons": total_lessons,
                "completed_lessons": completed_lessons,
            })

            # recent activity

        recent_activities = LessonProgress.objects.filter(user=request.user).select_related(
                "lesson", "lesson__module", "lesson__module__course").order_by("-last_accessed")[:3]

        recent_serializer = RecentActivitySerializer(recent_activities, many=True)

        return Response({
            "course_progress": course_progress_data,
            "recent_activities": recent_serializer.data
        })




############################################ Teacher Section ##############################


class TeacherDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        teacher = request.user

        courses = Course.objects.filter(teacher=teacher)
        approved_courses = courses.filter(is_published=True)
        pending_courses = courses.filter(is_published=False)

        course_data = []
        for course in approved_courses:
            total_students = Enrollment.objects.filter(course=course, is_active=True).count()
            course_data.append(
                {
                    "course_title": course.title,
                    "total_students": total_students
                }
            )

            return Response({
                "course_data": course_data,
                "approved_courses": [c.title for c in approved_courses],
                "pending_courses": [c.title for c in pending_courses]
            })


class CreateCourseTeacherAPIView(generics.CreateAPIView):
    serializer_class = CourseSerializer
    permission_class = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user, is_published=False)


class EditCourseTeacherAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)

        if course.teacher != request.user:
            return Response({
                "Error": "Not Allowed"
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = CourseSerializer(course, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class CreateModuleTeacherAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)

        if not course.is_published:
            return Response({
                "error": "Course not approved yet."
            })
        
        if course.teacher != request.user:
            return Response({
                "error": "Not Allowed"
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ModuleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(course=course)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class TeacherCourseDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        course = Course.objects.filter(teacher=request.user)
        serializer = CourseSerializer(course, many=True)
        return Response({
            "Courses": serializer.data
        }, status=status.HTTP_200_OK)
    

class CreateLessonTeacherAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, module_id):
        module = get_object_or_404(Module, id=module_id)
        course = module.course

        if not course.is_published():
            return Response({
                "error": "Course not approved yet."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if course.teacher != request.user:
            return Response({
                "error": 'You are not allowed.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = LessonSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(course=course)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


####################### Student Section ################################################

class StudentLearningDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # active enrollments
        user_enrollments = Enrollment.objects.filter(user=user, is_active=True).select_related('course')

        course_progress = []
        for enrollment in user_enrollments:
            course = enrollment.course
            total_lessons = Lesson.objects.filter(
                module__course = course,
                is_published = True
            ).count()
            completed_lessons = LessonProgress.objects.filter(
                user=user,
                lesson__module__course=course,
                is_completed=True
            ).count()

            progress_percentage = (
                (completed_lessons / total_lessons)*100 if total_lessons > 0 else 0
            )

            course_progress.append({
                "course_id": course.id,
                "course_title": course.title,
                "progress_percentage": round(progress_percentage,2),
                "total_lessons": total_lessons,
                "completed_lessons": completed_lessons,
                "enrollment_id": enrollment.id,
                # "enrolled_at": enrollment.created_at,
            })

            # recent activity

            recent_activities = LessonProgress.objects.filter(user=user).select_related(
                'lesson', 'lesson__module', 'lesson__module__course'
            ).order_by("-last_accessed")[:10]

            recent_progress = []
            for activity in recent_activities:
                recent_progress.append({
                    'lesson_id': activity.lesson.id,
                    'lesson_title': activity.lesson.title,
                    'module_title': activity.lesson.module.title,
                    'course_title': activity.lesson.module.course.title,
                    'is_completed': activity.is_completed,
                    'last_accessed': activity.last_accessed
                })
                return Response({
                    "courses_progress": course_progress,
                    "recent_progress": recent_progress
                })












class ResumeCourseStudentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        lessons = Lesson.objects.filter(module__course_id = course_id, is_published=True).order_by("module__order", "order")
        progress_qs= LessonProgress.objects.filter(user=request.user, lesson__in = lessons)

        incomplete = progress_qs.filter(is_completed=False).order_by("started_at").first()
        if incomplete:
            return Response({
                "resume_lesson_id": incomplete.lesson.id
            }, status=200)
        
        last_accessed = progress_qs.order_by("-started_at").first()
        if last_accessed:
            return Response({
                "resume_lesson_id": last_accessed.lesson.id,
                "resume_lesson": last_accessed.lesson.title,
            }, status=200)
        
        first_lesson = lessons.first()
        if first_lesson:
            return Response({
                "resume_lesson_id": first_lesson.id
            }, status=200)
        
        return Response({
            "course_id": course_id,
            "message": "No lessons found"
        }, status=200)
    


class MarkLessonCompleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, lesson_id):
        lesson = get_object_or_404(Lesson, id=lesson_id, is_published=True)
        progress, _ = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)

        if not progress.is_completed:
            progress.is_completed = True
            progress.completed_at = timezone.now()
            progress.save()

        return Response({
            "status": "success",
            "lesson_id": lesson.id
        }, status=status.HTTP_200_OK)
    


class UpdateTimeSpentStudentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, lesson_id):
        lesson = get_object_or_404(Lesson, id=lesson_id, is_published=True)
        time_spent = request.data.get("time_spent", 0)

        try:
            time_spent = int(time_spent)
        except(ValueError, TypeError):
            return Response({
                "status": "error",
                "message": "Invalid time value"
            }, status=400)
        
        progress, _ = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
        progress.time_spent_minutes += time_spent
        progress.save()

        return Response({
            "status": "success",
            "lesson_id": lesson.id,
            "time_spent_minuts": progress.time_spent_minutes
        }, status=200)