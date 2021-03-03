from rest_framework import serializers
from ExperimentManager.Models import RuleInterpreter
import ExperimentManager.Serializers.Tool as Tool


class RuleInterpreterSerializer(serializers.ModelSerializer):
    class Meta:
        model = RuleInterpreter
        fields = ['id', 'model_name', 'property_name', 'property_value']
        read_only = ['id']

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)

        super(RuleInterpreterSerializer, self).__init__(*args, **kwargs)

        Tool.drop_fields(self, fields)

    def create(self, validated_data):
        return RuleInterpreter.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.model_name = validated_data.get('model_name', instance.model_name)
        instance.property_name = validated_data.get('property_name', instance.property_name)
        instance.property_value = validated_data.get('property_value', instance.property_value)
        instance.save()
        return instance
