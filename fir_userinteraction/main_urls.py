from django.conf.urls import url, include

handler403 = 'fir_userinteraction.errors.permission_denied'

urlpatterns = [
    url(r'^', include('fir_userinteraction.urls', namespace="userinteraction"))
]
