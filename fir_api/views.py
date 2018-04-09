# for token Generation
import StringIO

from django.conf import settings
from django.db.models.signals import post_save
from django.http import HttpResponse
from django.dispatch import receiver
from django.shortcuts import get_object_or_404
from django.core.files import File as FileWrapper
from django.contrib.auth.models import User, Group

from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.authtoken.models import Token
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework import viewsets, status
from rest_framework.decorators import detail_route, list_route
from rest_framework import renderers
from rest_framework.response import Response

from fir_alerting.models import CategoryTemplate, RecipientTemplate
from fir_api.serializers import UserSerializer, IncidentSerializer, ArtifactSerializer, FileSerializer, \
    BusinessLineSerializer, RecipientTemplateSerializer, CategoryTemplateSerializer, AccessControlEntrySerializer, \
    GroupSerializer, CategorySerializer, DetectionSerializer
from fir_api.permissions import IsIncidentHandler
from fir_artifacts.files import handle_uploaded_file, do_download
from incidents.models import Incident, Artifact, Comments, File, BusinessLine, AccessControlEntry, IncidentCategory, \
    Label


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated, IsAdminUser)

    @list_route(methods=['get'], url_path='by_name/(?P<username>\w+)')
    def get_by_username(self, request, username):
        user = get_object_or_404(User, username=username)
        return Response(UserSerializer(user, context={'request': request}).data, status=status.HTTP_200_OK)


class IncidentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows creation of, viewing, and closing of incidents
    """
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)

    def perform_create(self, serializer):
        instance = serializer.save(opened_by=self.request.user)
        instance.refresh_main_business_lines()
        instance.done_creating()

    def perform_update(self, serializer):
        Comments.create_diff_comment(self.get_object(), serializer.validated_data, self.request.user)
        instance = serializer.save()
        instance.refresh_main_business_lines()


class BusinessLineViewSet(viewsets.ModelViewSet):
    queryset = BusinessLine.objects.all()
    serializer_class = BusinessLineSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)

    def get_queryset(self):
        queryset = BusinessLine.objects.all()
        name = self.request.query_params.get('name', None)
        if name is not None:
            queryset = queryset.filter(name=name)
        return queryset

    @list_route(methods=['get'], url_path='by_name/(?P<name>\w+)')
    def get_by_name(self, request, name):
        bl = get_object_or_404(BusinessLine, name=name)
        return Response(BusinessLineSerializer(bl, context={'request': request}).data, status=status.HTTP_200_OK)


class CategoryTemplateViewSet(viewsets.ModelViewSet):
    queryset = CategoryTemplate.objects.all()
    serializer_class = CategoryTemplateSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)


class RecipientTemplateViewSet(viewsets.ModelViewSet):
    queryset = RecipientTemplate.objects.all()
    serializer_class = RecipientTemplateSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)


class AccessControlEntryViewSet(viewsets.ModelViewSet):
    queryset = AccessControlEntry.objects.all()
    serializer_class = AccessControlEntrySerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)

    @list_route(methods=['get'], url_path='by_name/(?P<name>.+)')
    def get_by_name(self, request, name):
        gr = get_object_or_404(Group, name=name)
        return Response(GroupSerializer(gr, context={'request': request}).data, status=status.HTTP_200_OK)


class CategoriesViewSet(viewsets.ModelViewSet):
    queryset = IncidentCategory.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)


class DetectionViewSet(viewsets.ModelViewSet):
    queryset = Label.objects.filter(group__name='detection')
    serializer_class = DetectionSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)


class ArtifactViewSet(ListModelMixin, RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Artifact.objects.all()
    serializer_class = ArtifactSerializer
    lookup_field = 'value'
    lookup_value_regex = '.+'
    permission_classes = (IsAuthenticated, IsIncidentHandler)


class FileViewSet(ListModelMixin, RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)

    @detail_route(renderer_classes=[renderers.StaticHTMLRenderer])
    def download(self, request, pk):
        return do_download(request, pk)

    @detail_route(methods=["POST"])
    def upload(self, request, pk):
        files = request.data['files']
        incident = get_object_or_404(Incident, pk=pk)
        files_added = []
        for i, file in enumerate(files):
            file_obj = FileWrapper(StringIO.StringIO(file['content']))
            file_obj.name = file['filename']
            description = file['description']
            f = handle_uploaded_file(file_obj, description, incident)
            files_added.append(f)
        resp_data = FileSerializer(files_added, many=True, context={'request': request}).data
        return HttpResponse(JSONRenderer().render(resp_data), content_type='application/json')


# Token Generation ===========================================================

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
