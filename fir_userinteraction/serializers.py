from rest_framework import serializers

from fir_userinteraction.models import Quiz, QuizTemplate, QuizWatchListItem


class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ('id', 'incident', 'template', 'answers', 'is_answered', 'user')
        read_only_fields = ('id', 'answers', 'is_answered')


class QuizTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizTemplate
        fields = '__all__'
        read_only_fields = ['id']


class QuizWatchListItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizWatchListItem
        fields = '__all__'
        read_only_fields = ['id']


class EmailSerializer(serializers.Serializer):
    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

    emails = serializers.ListField(
        child=serializers.CharField(allow_null=False)
    )
    incident_id = serializers.IntegerField(allow_null=False)
    authorized = serializers.BooleanField()


class WatchlistSerializer(serializers.Serializer):
    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

    business_lines = serializers.ListField(
        child=serializers.IntegerField(allow_null=False)
    )
    form_id = serializers.CharField(allow_null=False)
    device = serializers.CharField(allow_null=False)
    name = serializers.CharField(allow_null=False)
    date = serializers.CharField(allow_null=False)
    file = serializers.CharField(allow_null=False)
    protocol = serializers.CharField(allow_null=False)
