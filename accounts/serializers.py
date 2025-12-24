from django.contrib.auth.models import User
from rest_framework import serializers
from courses.models import UserProfile

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