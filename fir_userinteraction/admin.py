from django.contrib import admin

# Register your models here.
from fir_userinteraction.models import Question, Quiz, QuizTemplate, QuizAnswer, QuestionGroup, QuizGroupQuestionOrder


class QuizGroupQuestionOrderInline(admin.TabularInline):
    model = QuizGroupQuestionOrder
    ordering = ['order_index']
    extra = 1


class QuestionGroupAdmin(admin.ModelAdmin):
    inlines = (QuizGroupQuestionOrderInline,)


admin.site.register(QuizTemplate)
admin.site.register(Quiz)
admin.site.register(QuizAnswer)
admin.site.register(QuestionGroup, QuestionGroupAdmin)
admin.site.register(Question)
