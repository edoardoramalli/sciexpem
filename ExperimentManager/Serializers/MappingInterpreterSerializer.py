from rest_framework import serializers
from ExperimentManager.Models import MappingInterpreter
import ExperimentManager.Serializers.Tool as Tool


class MappingInterpreterSerializer(serializers.ModelSerializer):
    class Meta:
        model = MappingInterpreter
        fields = ['id',
                  'x_exp_name', 'x_exp_location', 'x_sim_name', 'x_sim_location', 'x_transformation',
                  'y_exp_name', 'y_exp_location', 'y_sim_name', 'y_sim_location', 'y_transformation',
                  'file']
        read_only = ['id']

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)

        super(MappingInterpreterSerializer, self).__init__(*args, **kwargs)

        Tool.drop_fields(self, fields)

    def create(self, validated_data):
        return MappingInterpreter.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.x_exp_name = validated_data.get('x_exp_name', instance.x_exp_name)
        instance.x_exp_location = validated_data.get('x_exp_location', instance.x_exp_location)
        instance.x_sim_name = validated_data.get('x_sim_name', instance.x_sim_name)
        instance.x_sim_location = validated_data.get('x_sim_location', instance.x_sim_location)
        instance.x_transformation = validated_data.get('x_transformation', instance.x_transformation)
        instance.y_exp_name = validated_data.get('y_exp_name', instance.y_exp_name)
        instance.y_exp_location = validated_data.get('y_exp_location', instance.y_exp_location)
        instance.y_sim_name = validated_data.get('y_sim_name', instance.y_sim_name)
        instance.y_sim_location = validated_data.get('y_sim_location', instance.y_sim_location)
        instance.y_transformation = validated_data.get('y_transformation', instance.y_transformation)
        instance.file = validated_data.get('file', instance.file)
        instance.save()
        return instance
