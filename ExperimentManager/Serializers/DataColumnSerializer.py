from rest_framework import serializers
from ExperimentManager.Models import DataColumn
from ExperimentManager.Serializers import Tool


class DataColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataColumn
        fields = ['id', 'name', 'units', 'data', 'dg_id', 'label', 'species', 'nominal', 'plotscale', 'ignore']
        read_only = ['id']

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)

        super(DataColumnSerializer, self).__init__(*args, **kwargs)

        Tool.drop_fields(self, fields)

    def create(self, validated_data):
        return DataColumn.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.units = validated_data.get('units', instance.units)
        instance.data = validated_data.get('data', instance.data)
        instance.dg_id = validated_data.get('dg_id', instance.dg_id)
        instance.label = validated_data.get('label', instance.label)
        instance.species = validated_data.get('species', instance.species)
        instance.nominal = validated_data.get('nominal', instance.nominal)
        instance.plotscale = validated_data.get('plotscale', instance.plotscale)
        instance.ignore = validated_data.get('ignore', instance.ignore)
        instance.save()
        return instance
