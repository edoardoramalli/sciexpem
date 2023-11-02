from rest_framework import serializers
from ExperimentManager.Models import InitialSpecies
import ExperimentManager.Serializers as Serializers
import ExperimentManager.Serializers.Tool as Tool


class InitialSpeciesSerializer(serializers.ModelSerializer):
    species = Serializers.SpeciesSerializer(read_only=True)

    class Meta:
        model = InitialSpecies
        fields = ['id', 'species', 'units', 'value', 'source_type', 'configuration']
        read_only = ['id']

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)

        req = ['species']

        if fields is None:
            fields = tuple(req)

        super(InitialSpeciesSerializer, self).__init__(*args, **kwargs)

        Tool.drop_fields(self, fields)

    def create(self, validated_data):
        return InitialSpecies.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.units = validated_data.get('units', instance.units)
        instance.value = validated_data.get('value', instance.value)
        instance.save()
        return instance
