from rest_framework import serializers
from ExperimentManager.Models import ExecutionColumn
import ExperimentManager.Serializers as Serializers


class ExecutionColumnBackTrackSerializer(serializers.ModelSerializer):
    execution = Serializers.ExecutionSerializer()

    class Meta:
        model = ExecutionColumn
        fields = ['id', 'execution']
        read_only = ['id']

