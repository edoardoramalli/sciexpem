from rest_framework import serializers
from ExperimentManager.Models import Specie


class SpecieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specie
        fields = ['id', 'InChI', 'preferredKey', 'names', 'CAS', 'SMILES', 'chemName', 'formula']
        read_only_fields = ['id']