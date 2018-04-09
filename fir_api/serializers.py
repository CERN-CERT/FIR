from django.contrib.auth.models import User, Group
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from fir_alerting.models import CategoryTemplate, RecipientTemplate
from incidents.models import Incident, Artifact, Label, File, IncidentCategory, BusinessLine, AccessControlEntry


# serializes data from the FIR User model
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'email', 'groups')
        read_only_fields = ('id',)
        extra_kwargs = {'url': {'view_name': 'api:user-detail'}}


# FIR Artifact model
class ArtifactSerializer(serializers.ModelSerializer):
    incidents = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name='api:incident-detail')

    class Meta:
        model = Artifact
        fields = ('id', 'type', 'value', 'incidents')
        read_only_fields = ('id',)


# FIR File model

class AttachedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ('id', 'description', 'url')
        read_only_fields = ('id',)
        extra_kwargs = {'url': {'view_name': 'api:file-detail'}}


class FileSerializer(serializers.ModelSerializer):
    incident = serializers.HyperlinkedRelatedField(read_only=True, view_name='api:incident-detail')

    class Meta:
        model = File
        fields = ('id', 'description', 'incident', 'url', 'file')
        read_only_fields = ('id',)
        extra_kwargs = {'url': {'view_name': 'api:file-download'}}
        depth = 2


# FIR Incident model

class IncidentSerializer(serializers.ModelSerializer):
    detection = serializers.PrimaryKeyRelatedField(queryset=Label.objects.filter(group__name='detection'))
    actor = serializers.PrimaryKeyRelatedField(queryset=Label.objects.filter(group__name='actor'), required=False)
    plan = serializers.PrimaryKeyRelatedField(queryset=Label.objects.filter(group__name='plan'), required=False)
    file_set = AttachedFileSerializer(many=True, read_only=True)
    opened_by = serializers.ReadOnlyField(source='opened_by.username')
    concerned_business_lines_urls = serializers.HyperlinkedRelatedField(many=True, view_name='api:businessline-detail',
                                                                        read_only=True,
                                                                        source='concerned_business_lines')

    class Meta:
        model = Incident
        exclude = ['main_business_lines', 'artifacts']
        read_only_fields = ('id', 'opened_by', 'main_business_lines', 'file_set')


class CategoryTemplateSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='api:categorytemplate-detail', read_only=True)
    incident_category = serializers.PrimaryKeyRelatedField(queryset=IncidentCategory.objects.all())

    class Meta:
        fields = '__all__'
        model = CategoryTemplate


class RecipientTemplateSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='api:recipienttemplate-detail', read_only=True)
    business_line = serializers.HyperlinkedRelatedField(queryset=BusinessLine.objects.all(),
                                                        view_name='api:businessline-detail')

    class Meta:
        fields = '__all__'
        model = RecipientTemplate


class AccessControlEntrySerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='api:accesscontrolentry-detail', read_only=True)
    business_line = serializers.PrimaryKeyRelatedField(queryset=BusinessLine.objects.all())
    role = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        fields = '__all__'
        model = AccessControlEntry


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Group


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'name']
        read_only_fields = ['id']
        model = IncidentCategory


class DetectionSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'name']
        read_only_fields = ['id']
        model = Label


# FIR business line model
class BusinessLineSerializer(serializers.HyperlinkedModelSerializer):
    nested_name = serializers.CharField(source='__unicode__', read_only=True)
    name = serializers.CharField(required=True, max_length=100, allow_blank=False)
    url = serializers.HyperlinkedIdentityField(view_name='api:businessline-detail', read_only=True)
    parent_url = serializers.HyperlinkedRelatedField(allow_empty=True, read_only=True,
                                                     view_name='api:businessline-detail', source='get_parent')
    parent = serializers.PrimaryKeyRelatedField(queryset=BusinessLine.objects.all(),
                                                allow_null=True,
                                                allow_empty=True,
                                                source='get_parent')

    children = serializers.PrimaryKeyRelatedField(read_only=True,
                                                  allow_null=True,
                                                  allow_empty=True,
                                                  many=True,
                                                  source='get_children')

    children_urls = serializers.HyperlinkedRelatedField(allow_empty=True, read_only=True, many=True,
                                                        view_name='api:businessline-detail', source='get_children')

    def create(self, validated_data):
        name = validated_data['name']
        if 'get_parent' in validated_data and validated_data['get_parent'] is not None:
            parent_entity = validated_data['get_parent']
            bl = parent_entity.add_child(name=name)
        else:
            bl = BusinessLine.add_root(name=name)
        return BusinessLine.objects.get(id=bl.id)

    def update(self, instance, validated_data):
        parent = validated_data['get_parent']
        if parent is not None:
            instance.move(parent, 'first-child')
        else:
            first_root_node = BusinessLine.objects.filter(depth=1)[0]
            instance.move(first_root_node, 'first-sibling')

        # Work around django-treebeard "known-caveat", see http://django-treebeard.readthedocs.io/en/latest/caveats.html
        instance = BusinessLine.objects.get(id=instance.id)
        instance.name = validated_data['name']
        instance.save()
        return instance

    class Meta:
        fields = ['url', 'id', 'name', 'parent_url',
                  'nested_name', 'parent', 'children', 'children_urls']
        model = BusinessLine
