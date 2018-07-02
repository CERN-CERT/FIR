# API related stuff

import logging

from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from fir_api.permissions import IsIncidentHandler
from fir_userinteraction.helpers import build_userinteraction_path
from fir_userinteraction.models import Quiz, QuizTemplate, QuizWatchListItem, get_or_create_label, \
    create_artifact_for_incident
from fir_userinteraction.serializers import QuizSerializer, QuizTemplateSerializer, QuizWatchListItemSerializer, \
    WatchlistSerializer
from incidents.models import Comments, BusinessLine


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


class QuizWatchListItemViewSet(viewsets.ModelViewSet):
    queryset = QuizWatchListItem.objects.all()
    serializer_class = QuizWatchListItemSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)


@api_view(["POST"])
@permission_classes((IsAuthenticated, IsIncidentHandler))
def subscribe_to_watchlist(request):
    serializer = WatchlistSerializer(data=request.data)
    if serializer.is_valid():
        qz = Quiz.objects.get(id=serializer.validated_data['form_id'])
        for bl in serializer.validated_data['business_lines']:
            try:
                bl_obj = BusinessLine.objects.get(id=bl)
                QuizWatchListItem.objects.create(business_line=bl_obj, quiz=qz)
            except BusinessLine.DoesNotExist:
                logging.error('Business line: {} does not exist'.format(bl))

        incident = qz.incident
        incident.status = 'B'
        incident.save()

        create_artifact_for_incident(incident, artifact_type='incident_url',
                                     artifact_value=build_userinteraction_path(request, qz.incident_id))

        incident.save()
        Comments.objects.create(incident=incident,
                                comment='Initial notification sent',
                                action=get_or_create_label('Initial'),
                                opened_by=incident.opened_by)

        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
