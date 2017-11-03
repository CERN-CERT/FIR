from rest_framework import serializers

from fir_userinteraction.models import Quiz


class QuizSerializer(serializers.ModelSerializer):

    class Meta:
        model = Quiz
        fields = ('id', 'incident', 'template', 'answers', 'is_answered')
        read_only_fields = ('id', 'answers', 'is_answered')
