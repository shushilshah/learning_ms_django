# from django.db import models

# # Create your models here.
# from django.contrib.auth.models import User

# class UserProfile(models.Model):
#     ROLE_CHOICES = (
#         ("admin", "admin"),
#         ("student", "student"),
#         ("teacher", "teacher")
#     )

#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     role = models.CharField(max_length=255, choices=ROLE_CHOICES)

#     class Meta:
#         db_table = 'courses_userprofile'
#         # managed = False

#     def __str__(self):
#         return f"{self.user.username} - {self.role}"
    
