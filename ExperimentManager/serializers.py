from rest_framework import serializers

import ExperimentManager.Models as Model


class CommonPropertySerializerAPI(serializers.ModelSerializer):
    class Meta:
        model = Model.CommonProperty
        fields = '__all__'


class InitialSpecieSerializerAPI(serializers.ModelSerializer):
    class Meta:
        model = Model.InitialSpecie
        fields = '__all__'


class DataColumnSerializerAPI(serializers.ModelSerializer):
    class Meta:
        model = Model.DataColumn
        fields = '__all__'


class FilePaperSerializerAPI(serializers.ModelSerializer):
    class Meta:
        model = Model.FilePaper
        fields = '__all__'


class ExperimentSerializerAPI(serializers.ModelSerializer):
    data_columns = DataColumnSerializerAPI(many=True)
    file_paper = FilePaperSerializerAPI()
    initial_species = InitialSpecieSerializerAPI(many=True)
    common_properties = CommonPropertySerializerAPI(many=True)
    experimentClassifier = serializers.SerializerMethodField()

    class Meta:
        model = Model.Experiment
        fields = '__all__'

    def get_experimentClassifier(self, obj):
        return obj.experiment_interpreter


class ChemModelSerializerAPI(serializers.ModelSerializer):

    class Meta:
        model = Model.ChemModel
        fields = '__all__'


class ExecutionColumnSerializerAPI(serializers.ModelSerializer):

    class Meta:
        model = Model.ExecutionColumn
        fields = '__all__'


class ExecutionSerializerAPI(serializers.ModelSerializer):
    chemModel = ChemModelSerializerAPI()
    experiment = ExperimentSerializerAPI()
    execution_columns = ExecutionColumnSerializerAPI(many=True)

    class Meta:
        model = Model.Execution
        fields = '__all__'


# This class is a double but is necessary because when filter a CurveMatchingResult query
# I want also the serialization of the Execution object but when filter a Execution query
# I don't want the serialization of the Execution object, otherwise possible loop.
class ExecutionColumnSerializerBackTrackingAPI(serializers.ModelSerializer):
    execution = ExecutionSerializerAPI()

    class Meta:
        model = Model.ExecutionColumn
        fields = '__all__'


class CurveMatchingResultSerializerAPI(serializers.ModelSerializer):
    # execution_column = ExecutionColumnSerializerBackTrackingAPI()

    class Meta:
        model = Model.CurveMatchingResult
        fields = ('id', 'index', 'error')





