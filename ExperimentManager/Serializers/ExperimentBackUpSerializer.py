from rest_framework import serializers
from ExperimentManager.Models import ExperimentBackUp
import ExperimentManager.Serializers.Tool as Tool
import ExperimentManager.Serializers as Serializers


class ExperimentBackUpSerializer(serializers.ModelSerializer):
    chemModel = Serializers.ChemModelSerializer()
    experiment = Serializers.ExperimentSerializer()

    class Meta:
        model = ExperimentBackUp
        fields = ['id', 'chemModel', 'dateTime', 'experiment', 'parameter_name', 'parameter_value', 'parameter_unit']
        read_only = ['id']

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)

        # req = ['chemModel']

        req = []

        if fields is None:
            fields = tuple(req)
        elif req not in fields:
            fields = fields + tuple(req)

        super(ExperimentBackUpSerializer, self).__init__(*args, **kwargs)

        Tool.drop_fields(self, fields)
