from django.conf.urls import url, include
from rest_framework import routers

import views

# API stuff
router = routers.DefaultRouter(trailing_slash=False)
router.register(r'quizzes', views.QuizViewSet)

urlpatterns = [
    # See https://stackoverflow.com/a/18359032 for the Regex explanation
    # Unauthenticated view
    url(r'^quiz/(?P<id>[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12})/$',
        views.get_quiz_by_id, name='quiz'),
    # Authenticated view
    url(r'^incidents/(?P<incident_id>[0-9]+)/$', views.get_quiz_by_incident, name='quiz-by-incident'),
    url(r'^comment/(?P<incident_id>[0-9]+)/$', views.comment_on_quiz, name='comment'),
    url(r'^api/', include(router.urls)),
    url(r'^$', views.show_all_quizzes, name='all-quizzes')
]
