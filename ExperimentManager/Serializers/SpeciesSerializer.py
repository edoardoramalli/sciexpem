from rest_framework import serializers
from ExperimentManager.Models import Species
import ExperimentManager.Serializers.Tool as Tool


class SpeciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Species
        fields = ['id', 'InChI', 'preferredKey', 'names', 'CAS', 'SMILES', 'chemName', 'formula']
        read_only_fields = ['id']

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)

        req = ['id', 'preferredKey']

        if fields is None:
            fields = tuple(req)

        super(SpeciesSerializer, self).__init__(*args, **kwargs)

        Tool.drop_fields(self, fields)