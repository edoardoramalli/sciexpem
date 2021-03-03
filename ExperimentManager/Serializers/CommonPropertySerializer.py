from rest_framework import serializers
from ExperimentManager.Models import CommonProperty
import ExperimentManager.Serializers.Tool as Tool


class CommonPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = CommonProperty
        fields = ['id', 'name', 'units', 'value']
        read_only = ['id']

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)

        super(CommonPropertySerializer, self).__init__(*args, **kwargs)

        Tool.drop_fields(self, fields)

    def create(self, validated_data):
        return CommonProperty.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.units = validated_data.get('units', instance.units)
        instance.value = validated_data.get('value', instance.value)
        instance.save()
        return instance
