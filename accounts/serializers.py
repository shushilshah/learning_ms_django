from django.contrib.auth.models import User
from rest_framework import serializers
from courses.models import UserProfile
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