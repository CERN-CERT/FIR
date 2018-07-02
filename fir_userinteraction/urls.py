from django.conf.urls import url, include
from rest_framework import routers

import views
import api

# API stuff
router = routers.DefaultRouter(trailing_slash=False)
router.register(r'forms', api.QuizViewSet)
router.register(r'formtemplates', api.QuizTemplatesViewSet)
router.register(r'formwatchlist', api.QuizWatchListItemViewSet)

urlpatterns = [
    # See https://stackoverflow.com/a/18359032 for the Regex explanation
    # Unauthenticated view
    url(r'^form/(?P<id>[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12})/$',
        views.get_quiz_by_id, name='quiz'),
    # Authenticated view
    url(r'^incidents/(?P<incident_id>[0-9]+)/$', views.get_quiz_by_incident, name='quiz-by-incident'),
    url(r'^comment/(?P<incident_id>[0-9]+)/$', views.comment_on_quiz, name='comment'),
    url(r'^api/', include(router.urls)),
    url(r'^api/watchlist', api.subscribe_to_watchlist, name='watchlist-api'),
    url(r'^$', views.show_all_quizzes, name='all-quizzes'),
    # OAuth endpoints for the standalone version
    url(r'^oauth/', include('oauth2_sso.urls'))
]
