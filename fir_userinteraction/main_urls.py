from django.conf.urls import url, include

urlpatterns = [
    url(r'^', include('fir_userinteraction.urls', namespace="userinteraction"))
]