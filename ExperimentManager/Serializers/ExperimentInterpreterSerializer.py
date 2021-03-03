from rest_framework import serializers
from ExperimentManager.Models import ExperimentInterpreter
import ExperimentManager.Serializers.Tool as Tool


class ExperimentInterpreterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperimentInterpreter
        fields = ['id', 'name', 'model_type', 'solver']
        read_only = ['id']

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)

        super(ExperimentInterpreterSerializer, self).__init__(*args, **kwargs)

        Tool.drop_fields(self, fields)

    def create(self, validated_data):
        return ExperimentInterpreter.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.model_type = validated_data.get('model_type', instance.model_type)
        instance.solver = validated_data.get('solver', instance.solver)
        instance.save()
        return instance
