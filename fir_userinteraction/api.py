# API related stuff
import json
from functools import reduce

import markdown2
from django.conf import settings
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.template import Context, Template
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from fir_api.permissions import IsIncidentHandler
from fir_plugins.links import Links
from fir_userinteraction.models import Quiz, QuizTemplate, QuizWatchListItem, CommentAttachment, get_or_create_label
from fir_userinteraction.serializers import QuizSerializer, QuizTemplateSerializer, EmailSerializer, \
    QuizWatchListItemSerializer, WatchlistSerializer
from fir_userinteraction.views import build_userinteraction_path
from incidents.models import Comments


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


@api_view(['POST'])
def send_account_emails(request):
    """
    List all code snippets, or create a new snippet.
    """
    serializer = EmailSerializer(data=request.data)
    if serializer.is_valid():
        print(serializer.validated_data)

        qz = get_object_or_404(Quiz, incident__id=serializer.validated_data['incident_id'])
        base_url = request.build_absolute_uri()
        if not settings.EXTERNAL_URL:
            site_root = '/'.join(base_url.split('/')[:3])
        else:
            site_root = settings.EXTERNAL_URL

        if serializer.validated_data['authorized']:
            incident_url = site_root + reverse('userinteraction:quiz-by-incident', args=[qz.incident_id])
        else:
            incident_url = site_root + reverse('userinteraction:quiz', args=[qz.id])

        incident_url = '[Incident URL]({})'.format(incident_url)
        affected_entities = reduce(lambda x, y: str(x) + ', ' + str(y),
                                   list(qz.incident.concerned_business_lines.all()))
        # TODO change template to be something more dynamic
        template = '# {subj}\n\n## Description:\n\n- {desc}\n\n## Category:\n\n{category}\n\n## Affected entities: ' \
                   '\n\n- {entities} \n\n\nYou ' \
                   'can access your incident by clicking here: {inc_url}' \
            .format(
            subj=qz.incident.subject,
            desc=qz.incident.description,
            category=qz.incident.category,
            entities=affected_entities,
            inc_url=incident_url)

        html = markdown2.markdown(template, extras=["link-patterns", "tables", "code-friendly"],
                                  link_patterns=Links().link_patterns())
        c = Context({'template': html})
        rendered = Template("{{ template | safe }}\n\n").render(c)
        send_mail('[FIR Incidents] A security incident is waiting for your feedback', html_message=rendered,
                  from_email='noreply@cern.ch',
                  message='This message is generated automatically by FIR',
                  recipient_list=serializer.validated_data['emails'])

        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def subscribe_to_watchlist(request):
    serializer = WatchlistSerializer(data=request.data)
    if serializer.is_valid():
        qz = Quiz.objects.get(id=serializer.validated_data['form_id'])
        for mail in serializer.validated_data['emails']:
            QuizWatchListItem.objects.create(email=mail, quiz=qz)

        extra_data = {
            'name': serializer.validated_data['name'],
            'device': serializer.validated_data['device'],
            'date': serializer.validated_data['date'],
            'file': serializer.validated_data['file'],
            'protocol': serializer.validated_data['protocol'],
            'incident_url': build_userinteraction_path(request, qz.incident_id)
        }
        incident = qz.incident
        incident.status = 'B'
        incident.save()

        comment = Comments.objects.create(incident=incident,
                                          comment='Initial notification sent',
                                          action=get_or_create_label('Initial'),
                                          opened_by=incident.opened_by)
        CommentAttachment.objects.create(comment=comment, attachment=json.dumps(extra_data))

        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
