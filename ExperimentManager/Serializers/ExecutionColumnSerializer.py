from rest_framework import serializers
from ExperimentManager.Models import ExecutionColumn
from ExperimentManager.Serializers import Tool


class ExecutionColumnSerializer(serializers.ModelSerializer):

    class Meta:
        model = ExecutionColumn
        fields = ['id', 'name', 'units', 'species', 'data', 'label', 'file_type']
        read_only = ['id']

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)

        super(ExecutionColumnSerializer, self).__init__(*args, **kwargs)

        Tool.drop_fields(self, fields)

    def create(self, validated_data):
        return ExecutionColumn.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.units = validated_data.get('units', instance.units)
        instance.species = validated_data.get('species', instance.species)
        instance.data = validated_data.get('data', instance.data)
        instance.label = validated_data.get('label', instance.label)
        instance.file_type = validated_data.get('file_type', instance.file_type)
        instance.save()
        return instance