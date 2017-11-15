# API related stuff
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from fir_api.permissions import IsIncidentHandler
from fir_userinteraction.models import Quiz, QuizTemplate
from fir_userinteraction.serializers import QuizSerializer, QuizTemplateSerializer


class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)

    class Meta:
        fields = '__all__'


class QuizTemplatesViewSet(viewsets.ModelViewSet):
    queryset = QuizTemplate.objects.all()
    serializer_class = QuizTemplateSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)
