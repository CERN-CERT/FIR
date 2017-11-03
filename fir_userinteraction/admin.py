from django.contrib import admin

# Register your models here.
from fir_userinteraction.models import Question, Quiz, QuizTemplate, QuizAnswer

admin.site.register(QuizTemplate)
admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(QuizAnswer)
