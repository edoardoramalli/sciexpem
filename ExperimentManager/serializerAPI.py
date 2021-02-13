from rest_framework import serializers
import ExperimentManager.models as M


class NewCommonPropertySerializerAPI(serializers.ModelSerializer):
    class Meta:
        model = M.CommonProperty
        fields = ['id']


class NewInitialSpecieSerializerAPI(serializers.ModelSerializer):
    class Meta:
        model = M.InitialSpecie
        fields = ['id']


class NewDataColumnSerializerAPI(serializers.ModelSerializer):
    class Meta:
        model = M.DataColumn
        fields = ['id']


class NewFilePaperSerializerAPI(serializers.ModelSerializer):
    class Meta:
        model = M.FilePaper
        fields = ['id']


class NewExperimentSerializerAPI(serializers.ModelSerializer):
    data_columns = NewDataColumnSerializerAPI(many=True)
    file_paper = NewFilePaperSerializerAPI()
    initial_species = NewInitialSpecieSerializerAPI(many=True)
    common_properties = NewCommonPropertySerializerAPI(many=True)
    # experimentClassifier = serializers.SerializerMethodField()

    class Meta:
        model = M.Experiment
        fields = ['id', 'data_columns', 'file_paper', 'initial_species', 'common_properties']

    # def get_experimentClassifier(self, obj):
    #     return obj.experiment_classifier


class NewChemModelSerializerAPI(serializers.ModelSerializer):

    class Meta:
        model = M.ChemModel
        fields = ['id']


class NewExecutionColumnSerializerAPI(serializers.ModelSerializer):
    # execution = NewExecutionSerializerAPI()

    class Meta:
        model = M.ExecutionColumn
        fields = ['id']



class NewExecutionSerializerAPI(serializers.ModelSerializer):
    chemModel = NewChemModelSerializerAPI()
    experiment = NewExperimentSerializerAPI()
    execution_columns = NewExecutionColumnSerializerAPI(many=True)

    class Meta:
        model = M.Execution
        fields = ['id', 'chemModel', 'experiment', 'execution_columns']





# This class is a double but is necessary because when filter a CurveMatchingResult query
# I want also the serialization of the Execution object but when filter a Execution query
# I don't want the serialization of the Execution object, otherwise possible loop.
class NewExecutionColumnSerializerBackTrackingAPI(serializers.ModelSerializer):
    execution = NewExecutionSerializerAPI()

    class Meta:
        model = M.ExecutionColumn
        fields = ['id', 'execution']


class NewCurveMatchingResultSerializerAPI(serializers.ModelSerializer):
    execution_column = NewExecutionColumnSerializerBackTrackingAPI()

    class Meta:
        model = M.CurveMatchingResult
        fields = ['id', 'index', 'error', 'execution_column']


class NewRuleClassifierSerializerAPI(serializers.ModelSerializer):
    class Meta:
        model = M.RuleClassifier
        fields = ['id']


class NewMappingClassifierSerializerAPI(serializers.ModelSerializer):
    class Meta:
        model = M.MappingClassifier
        fields = ['id']


class NewExperimentClassifierSerializerAPI(serializers.ModelSerializer):
    rules = NewRuleClassifierSerializerAPI(many=True)
    mappings = NewMappingClassifierSerializerAPI(many=True)

    class Meta:
        model = M.ExperimentClassifier
        fields = ['id', 'rules', 'mappings']


