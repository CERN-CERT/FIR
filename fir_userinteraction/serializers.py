from rest_framework import serializers

from fir_userinteraction.models import Quiz, QuizTemplate


class QuizSerializer(serializers.ModelSerializer):

    class Meta:
        model = Quiz
        fields = ('id', 'incident', 'template', 'answers', 'is_answered')
        read_only_fields = ('id', 'answers', 'is_answered')


class QuizTemplateSerializer(serializers.ModelSerializer):

    class Meta:
        model = QuizTemplate
        fields = '__all__'
        read_only_fields = ['id']
