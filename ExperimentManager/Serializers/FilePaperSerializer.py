from rest_framework import serializers
from ExperimentManager.Models import FilePaper
import ExperimentManager.Serializers.Tool as Tool


class FilePaperSerializer(serializers.ModelSerializer):
    class Meta:
        model = FilePaper
        fields = ['id', 'references', 'reference_doi']
        read_only_fields = ['id']

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)

        super(FilePaperSerializer, self).__init__(*args, **kwargs)

        Tool.drop_fields(self, fields)

    def create(self, validated_data):
        return FilePaper.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.references = validated_data.get('references', instance.references)
        instance.reference_doi = validated_data.get('reference_doi', instance.reference_doi)
        instance.save()
        return instance
