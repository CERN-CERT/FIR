from django.contrib import admin

# Register your models here.
from fir_userinteraction.models import Question, Quiz, QuizTemplate, QuizAnswer, QuestionGroup, QuizGroupQuestionOrder, \
    QuizTemplateQuestionGroupOrder, QuizWatchListItem, QuizTemplateUsefulLink, UsefulLinkOrdering, AutoNotifyDuration


class QuizGroupQuestionOrderInline(admin.TabularInline):
    model = QuizGroupQuestionOrder
    ordering = ['order_index']
    extra = 1


class QuizTemplateQuestionGroupOrderInline(admin.TabularInline):
    model = QuizTemplateQuestionGroupOrder
    ordering = ['order_index']
    extra = 1


class UsefulLinkInline(admin.TabularInline):
    model = UsefulLinkOrdering
    ordering = ['order_index']
    extra = 1


class QuestionGroupAdmin(admin.ModelAdmin):
    inlines = (QuizGroupQuestionOrderInline,)


class QuizTemplateAdmin(admin.ModelAdmin):
    inlines = (QuizTemplateQuestionGroupOrderInline, UsefulLinkInline,)


class AutoNotifyDurationAdmin(admin.ModelAdmin):
    """
    This entity is used to configure the renotification period of each category and severity type
    """
    search_fields = ('category__name',)
    list_display = ['id', 'get_category_name', 'severity', 'duration']
    ordering = ['category__name', 'severity']

    def get_category_name(self, obj):
        return obj.category.name

    get_category_name.short_description = 'Category'


class QuizWatchListItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'business_line', 'get_quiz_id']
    search_fields = ('business_line__name',)
    ordering = ['business_line__name']

    def get_quiz_id(self, obj):
        return obj.quiz.id
    get_quiz_id.short_description = 'Quiz ID'


admin.site.register(QuizTemplate, QuizTemplateAdmin)
admin.site.register(QuestionGroup, QuestionGroupAdmin)
admin.site.register(AutoNotifyDuration, AutoNotifyDurationAdmin)
admin.site.register(QuizWatchListItem, QuizWatchListItemAdmin)
admin.site.register(Quiz)
admin.site.register(QuizAnswer)
admin.site.register(Question)
admin.site.register(QuizTemplateUsefulLink)
