from django.contrib import admin

# Register your models here.
from fir_userinteraction.models import Question, Quiz, QuizTemplate, QuizAnswer, QuestionGroup, QuizGroupQuestionOrder, \
    QuizTemplateQuestionGroupOrder


class QuizGroupQuestionOrderInline(admin.TabularInline):
    model = QuizGroupQuestionOrder
    ordering = ['order_index']
    extra = 1


class QuizTemplateQuestionGroupOrderInline(admin.TabularInline):
    model = QuizTemplateQuestionGroupOrder
    ordering = ['order_index']
    extra = 1


class QuestionGroupAdmin(admin.ModelAdmin):
    inlines = (QuizGroupQuestionOrderInline,)


class QuizTemplateAdmin(admin.ModelAdmin):
    inlines = (QuizTemplateQuestionGroupOrderInline,)


admin.site.register(QuizTemplate, QuizTemplateAdmin)
admin.site.register(QuestionGroup, QuestionGroupAdmin)
admin.site.register(Quiz)
admin.site.register(QuizAnswer)
admin.site.register(Question)
