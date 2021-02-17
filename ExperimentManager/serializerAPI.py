from rest_framework import serializers
import ExperimentManager.Models as Model
from ExperimentManager.models import *


class NewCommonPropertySerializerAPI(serializers.ModelSerializer):
    class Meta:
        model = Model.CommonProperty
        fields = ['id']


class NewInitialSpecieSerializerAPI(serializers.ModelSerializer):
    class Meta:
        model = Model.InitialSpecie
        fields = ['id']


class NewDataColumnSerializerAPI(serializers.ModelSerializer):
    class Meta:
        model = Model.DataColumn
        fields = ['id']


class NewFilePaperSerializerAPI(serializers.ModelSerializer):
    class Meta:
        model = Model.FilePaper
        fields = ['id']


class NewExperimentSerializerAPI(serializers.ModelSerializer):
    data_columns = NewDataColumnSerializerAPI(many=True)
    file_paper = NewFilePaperSerializerAPI()
    initial_species = NewInitialSpecieSerializerAPI(many=True)
    common_properties = NewCommonPropertySerializerAPI(many=True)
    # experimentClassifier = serializers.SerializerMethodField()

    class Meta:
        model = Model.Experiment
        fields = ['id', 'data_columns', 'file_paper', 'initial_species', 'common_properties']

    # def get_experimentClassifier(self, obj):
    #     return obj.experiment_classifier


class NewChemModelSerializerAPI(serializers.ModelSerializer):

    class Meta:
        model = Model.ChemModel
        fields = ['id']


class NewExecutionColumnSerializerAPI(serializers.ModelSerializer):
    # execution = NewExecutionSerializerAPI()

    class Meta:
        model = Model.ExecutionColumn
        fields = ['id']



class NewExecutionSerializerAPI(serializers.ModelSerializer):
    chemModel = NewChemModelSerializerAPI()
    experiment = NewExperimentSerializerAPI()
    execution_columns = NewExecutionColumnSerializerAPI(many=True)

    class Meta:
        model = Model.Execution
        fields = ['id', 'chemModel', 'experiment', 'execution_columns']





# This class is a double but is necessary because when filter a CurveMatchingResult query
# I want also the serialization of the Execution object but when filter a Execution query
# I don't want the serialization of the Execution object, otherwise possible loop.
class NewExecutionColumnSerializerBackTrackingAPI(serializers.ModelSerializer):
    execution = NewExecutionSerializerAPI()

    class Meta:
        model = Model.ExecutionColumn
        fields = ['id', 'execution']


class NewCurveMatchingResultSerializerAPI(serializers.ModelSerializer):
    execution_column = NewExecutionColumnSerializerBackTrackingAPI()

    class Meta:
        model = Model.CurveMatchingResult
        fields = ['id', 'error', 'score', 'execution_column']


class NewRuleInterpreterSerializerAPI(serializers.ModelSerializer):
    class Meta:
        model = RuleInterpreter
        fields = ['id']


class NewMappingInterpreterSerializerAPI(serializers.ModelSerializer):
    class Meta:
        model = MappingInterpreter
        fields = ['id']


class NewExperimentInterpreterSerializerAPI(serializers.ModelSerializer):
    rules = NewRuleInterpreterSerializerAPI(many=True)
    mappings = NewMappingInterpreterSerializerAPI(many=True)

    class Meta:
        model = ExperimentInterpreter
        fields = ['id', 'rules', 'mappings']


