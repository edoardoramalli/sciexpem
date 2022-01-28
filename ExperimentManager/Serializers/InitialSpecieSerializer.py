from rest_framework import serializers
from ExperimentManager.Models import InitialSpecie
import ExperimentManager.Serializers as Serializers
import ExperimentManager.Serializers.Tool as Tool


class InitialSpecieSerializer(serializers.ModelSerializer):
    specie = Serializers.SpecieSerializer(read_only=True)

    class Meta:
        model = InitialSpecie
        fields = ['id', 'specie', 'units', 'value', 'source_type']
        read_only = ['id']

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)

        req = ['specie']

        if fields is None:
            fields = tuple(req)

        super(InitialSpecieSerializer, self).__init__(*args, **kwargs)

        Tool.drop_fields(self, fields)

    def create(self, validated_data):
        return InitialSpecie.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.units = validated_data.get('units', instance.units)
        instance.value = validated_data.get('value', instance.value)
        instance.save()
        return instance
