from django.conf.urls import url
from .views import get_name

urlpatterns = [
    url(r'^quiz/', get_name, name='quiz')
]
