from rest_framework import serializers
from ExperimentManager.Models import Specie
import ExperimentManager.Serializers.Tool as Tool


class SpecieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specie
        fields = ['id', 'InChI', 'preferredKey', 'names', 'CAS', 'SMILES', 'chemName', 'formula']
        read_only_fields = ['id']

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)

        req = ['id', 'preferredKey']

        if fields is None:
            fields = tuple(req)

        super(SpecieSerializer, self).__init__(*args, **kwargs)

        Tool.drop_fields(self, fields)