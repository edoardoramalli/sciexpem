from rest_framework import serializers
from ExperimentManager.Models import Execution
from ExperimentManager.Serializers import Tool
from ExperimentManager.Serializers import *


class ExecutionSerializer(serializers.ModelSerializer):
    chemModel = ChemModelSerializer()
    experiment = ExperimentSerializer()
    execution_columns = ExecutionColumnSerializer(many=True)

    class Meta:
        model = Execution
        fields = ['id', 'chemModel', 'experiment', 'execution_start', 'execution_end', 'username']
        read_only = ['id']

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)

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