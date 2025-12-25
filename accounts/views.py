from rest_framework import status, views, generics
from rest_framework.response import Response
from .serializers import SignupSerializer, CourseSerializer
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from courses.models import Course, Enrollment
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView



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