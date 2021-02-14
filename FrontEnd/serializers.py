from rest_framework import serializers
from ExperimentManager.Models import *


class CommonPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = CommonProperty
        fields = '__all__'


class InitialSpecieSerializer(serializers.ModelSerializer):
    class Meta:
        model = InitialSpecie
        fields = '__all__'


class DataColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataColumn
        fields = '__all__'


class FilePaperSerializer(serializers.ModelSerializer):
    class Meta:
        model = FilePaper
        fields = '__all__'


class ExperimentSerializer(serializers.ModelSerializer):
    common_properties = CommonPropertySerializer(many=True, read_only=True)
    initial_species = InitialSpecieSerializer(many=True, read_only=True)
    file_paper = FilePaperSerializer(read_only=True)

    class Meta:
        model = Experiment
        fields = ('id', 'reactor', 'experiment_type',
                  'fileDOI', 'file_paper', 'common_properties',
                  'initial_species', 'ignition_type', 'status', 'experiment_interpreter',
                  'fuels', 'phi_inf', 'phi_sup', 't_inf', 't_sup', 'p_inf', 'p_sup')


class ChemModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChemModel
        fields = ('id', 'name')


class ExperimentDetailSerializer(serializers.ModelSerializer):
    common_properties = CommonPropertySerializer(many=True, read_only=True)
    initial_species = InitialSpecieSerializer(many=True, read_only=True)
    data_columns = DataColumnSerializer(many=True, read_only=True)

    class Meta:
        model = Experiment
        fields = ('id', 'reactor', 'experiment_type', 'fileDOI', 'file_paper', 'common_properties', 'initial_species', 'data_columns')


