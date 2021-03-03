from rest_framework import serializers
from ExperimentManager.Models import Execution
import ExperimentManager.Serializers.Tool as Tool
import ExperimentManager.Serializers as Serializers


class ExecutionSerializer(serializers.ModelSerializer):
    chemModel = Serializers.ChemModelSerializer()
    experiment = Serializers.ExperimentSerializer()
    execution_columns = Serializers.ExecutionColumnSerializer(many=True)

    class Meta:
        model = Execution
        fields = ['id', 'chemModel', 'experiment', 'execution_start', 'execution_end', 'username', 'execution_columns']
        read_only = ['id']

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)

        req = ['chemModel', 'experiment', 'execution_columns']

        if fields is None:
            fields = tuple(req)
        elif req not in fields:
            fields = fields + tuple(req)

        super(ExecutionSerializer, self).__init__(*args, **kwargs)

        Tool.drop_fields(self, fields)

    def create(self, validated_data):
        return Execution.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.chemModel = validated_data.get('chemModel', instance.chemModel)
        instance.experiment = validated_data.get('experiment', instance.experiment)
        instance.execution_start = validated_data.get('execution_start', instance.execution_start)
        instance.execution_end = validated_data.get('execution_end', instance.execution_end)
        instance.username = validated_data.get('username', instance.username)
        instance.save()
        return instance
