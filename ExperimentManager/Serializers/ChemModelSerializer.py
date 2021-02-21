from rest_framework import serializers
from ExperimentManager.Models import ChemModel
from ExperimentManager.Serializers import Tool


class ChemModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChemModel
        fields = ['id', 'name', 'xml_file_kinetics', 'xml_file_reaction_names', 'version']
        read_only = ['id']

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)

        super(ChemModelSerializer, self).__init__(*args, **kwargs)

        Tool.drop_fields(self, fields)

    def create(self, validated_data):
        return ChemModel.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.xml_file_kinetics = validated_data.get('xml_file_kinetics', instance.xml_file_kinetics)
        instance.xml_file_reaction_names = validated_data.get('xml_file_reaction_names', instance.xml_file_reaction_names)
        instance.version = validated_data.get('version', instance.version)
        instance.save()
        return instance