from django import forms
from courses.models import Course, Module, Lesson, Quiz, Question, Choice


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
        fields = ['course', 'title', 'order', 'is_published']


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['module', 'title', 'lesson_type', 'content',
                  'external_link', 'order', 'is_published', 'duration_minutes']

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


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['quiz', 'question_text', 'question_type', 'order', 'points']


class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['question', 'choice_text', 'is_correct', 'order']
