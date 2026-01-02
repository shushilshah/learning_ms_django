from rest_framework.permissions import BasePermission

class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        return request.user.userprofile.role == 'teacher'

class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return request.user.userprofile.role == 'student'

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.userprofile.role == 'admin'