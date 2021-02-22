from rest_framework import serializers
from ExperimentManager.Models import Experiment
import ExperimentManager.Serializers.Tool as Tool
import ExperimentManager.Serializers as Serializers


class ExperimentSerializer(serializers.ModelSerializer):
    common_properties = Serializers.CommonPropertySerializer(many=True, read_only=True)
    initial_species = Serializers.InitialSpecieSerializer(many=True, read_only=True)
    file_paper = Serializers.FilePaperSerializer(read_only=True)
    data_columns = Serializers.DataColumnSerializer(many=True)

    class Meta:
        model = Experiment
        fields = ['id', 'reactor', 'experiment_type', 'fileDOI', 'file_paper', 'ignition_type', 'xml_file',
                  'os_input_file', 'comment', 'fuels', 'status', 'common_properties', 'initial_species', 'data_columns',
                  'phi_inf', 'phi_sup', 't_inf', 't_sup', 'p_inf', 'p_sup', 'username']
        read_only = ['id']

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)

        req = ['common_properties', 'initial_species', 'data_columns', 'common_properties', 'file_paper']

        if fields is None:
            fields = tuple(req)
        elif req not in fields:
            fields = fields + tuple(req)

        super(ExperimentSerializer, self).__init__(*args, **kwargs)

        Tool.drop_fields(self, fields)

    def create(self, validated_data):
        return Experiment.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.reactor = validated_data.get('reactor', instance.reactor)
        instance.experiment_type = validated_data.get('experiment_type', instance.experiment_type)
        instance.fileDOI = validated_data.get('fileDOI', instance.fileDOI)
        instance.file_paper = validated_data.get('file_paper', instance.file_paper)
        instance.ignition_type = validated_data.get('ignition_type', instance.ignition_type)
        instance.xml_file = validated_data.get('xml_file', instance.xml_file)
        instance.os_input_file = validated_data.get('os_input_file', instance.os_input_file)
        instance.comment = validated_data.get('comment', instance.comment)
        instance.fuels = validated_data.get('fuels', instance.fuels)
        instance.phi_inf = validated_data.get('phi_inf', instance.phi_inf)
        instance.phi_sup = validated_data.get('phi_sup', instance.phi_sup)
        instance.t_inf = validated_data.get('t_inf', instance.t_inf)
        instance.t_sup = validated_data.get('t_sup', instance.t_sup)
        instance.p_inf = validated_data.get('p_inf', instance.p_inf)
        instance.p_sup = validated_data.get('p_sup', instance.p_sup)
        instance.username = validated_data.get('username', instance.username)
        instance.save()
        return instance
