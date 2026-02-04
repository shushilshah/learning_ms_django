from django import forms
from courses.models import Course, Module, Lesson, Quiz, Question, AnswerOption
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from notifications.models import Notification

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description',
                  'price', 'is_published', 'prerequistes']
        widgets = {
            'prerequistes': forms.CheckboxSelectMultiple,
        }


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['title', 'order', 'is_published']  # here if using form.as_p in template then must include 'course' field if not then exclude that


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'lesson_type', 'content',
                  'external_link', 'order', 'is_published', 'duration_minutes']  # also here if using form.as_p in template then include 'module' field if not then exclude

    def clean(self):
        cleaned_data = super().clean()
        lesson_type = cleaned_data.get('lesson_type')

        # if lesson_type == 'video' and not cleaned_data.get('video_url'):
        #     raise forms.ValidationError(
        #         "Video URL is required for video lessons")
        if lesson_type == 'external' and not cleaned_data.get('external_url'):
            raise forms.ValidationError(
                "External URL is required for external lessons.")

        return cleaned_data


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'course', 'module','description', 'time_limit_minutes', 'passing_score', 'is_published']


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['quiz', 'question_text', 'question_type', 'order', 'points']


class AnswerOptionForm(forms.ModelForm):
    class Meta:
        model = AnswerOption
        fields = ['question', 'choice_text', 'order']



class ChoiceBuldkForm(forms.Form):
    choice1 = forms.CharField()
    choice2 = forms.CharField()
    choice3 = forms.CharField()
    choice4 = forms.CharField()

    correct_choice = forms.ChoiceField(
        choices = [
            ('1', "Choice 1"),
            ('2', "Choice 2"),
            ('3', "Choice 3"),
            ('4', "Choice 4"),
        ],
        widget = forms.RadioSelect
    )


class SignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already in use")
        return email

class EditCourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description',
                  'price', 'is_published', 'prerequistes']


class AdminNotificationForm(forms.ModelForm):
    # RECEIVER_CHOICES = [
    #     ("teacher", "Teacher"),
    # ]

    # receiver_group = forms.ChoiceField(
    #     choices=RECEIVER_CHOICES,
    #     label="Receiver",
    #     required=True
    # )

    class Meta:
        model = Notification
        fields = ("title", "message")
