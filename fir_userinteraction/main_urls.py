from django.conf.urls import url, include

handler403 = 'fir_userinteraction.errors.permission_denied'
handler500 = 'fir_userinteraction.errors.internal_server_error'
handler404 = 'fir_userinteraction.errors.not_found'

urlpatterns = [
    url(r'^', include('fir_userinteraction.urls', namespace="userinteraction"))
]
