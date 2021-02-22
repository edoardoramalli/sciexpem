from rest_framework import serializers
from ExperimentManager.Models import CurveMatchingResult
import ExperimentManager.Serializers.Tool as Tool
import ExperimentManager.Serializers as Serializers


class CurveMatchingResultSerializer(serializers.ModelSerializer):
    execution_column = Serializers.ExecutionColumnBackTrackSerializer()

    class Meta:
        model = CurveMatchingResult
        fields = ['id', 'error', 'score', 'execution_column']

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)

        req = ['error', 'score', 'execution_column']

        if fields is None:
            fields = tuple(req)
        elif req not in fields:
            fields = fields + tuple(req)

        super(CurveMatchingResultSerializer, self).__init__(*args, **kwargs)

        Tool.drop_fields(self, fields)
