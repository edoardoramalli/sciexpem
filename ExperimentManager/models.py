# Django import
from django.db import models
import ExperimentManager.Models.Tool as Tool


class LoggerModel(models.Model):
    model_name = models.CharField(max_length=100)
    pk_model = models.IntegerField()
    username = models.CharField(max_length=100)
    action = models.CharField(max_length=50)
    date = models.DateTimeField()


class ExperimentClassifier(models.Model):
    name = models.CharField(max_length=100, unique=True)
    model_type = models.CharField(max_length=100)
    solver = models.CharField(max_length=100)

    def save(self, *args, **kwargs):
        kwargs['object'] = self
        Tool.generic_save(*args, **kwargs)

    @staticmethod
    def createExperimentClassifier(text_dict):
        name = text_dict['name']
        model_type = text_dict['model_type']
        solver = text_dict['solver']
        experiment_classifier = ExperimentClassifier(name=name, model_type=model_type, solver=solver)

        mappings = text_dict['mappings']
        tmp1 = [MappingClassifier.createMappingClassifier(mapping, experiment_classifier) for mapping in mappings]

        rules = text_dict['rules']
        tmp2 = [RuleClassifier.createRuleClassifier(rule, experiment_classifier) for rule in rules]

        return [experiment_classifier] + tmp1 + tmp2


class RuleClassifier(models.Model):
    model_name = models.CharField(max_length=100)
    property_name = models.CharField(max_length=100)
    property_value = models.CharField(max_length=100)
    experiment_classifier = models.ForeignKey(ExperimentClassifier, on_delete=models.CASCADE, related_name="rules")

    def save(self, *args, **kwargs):
        if 'username' in kwargs:
            kwargs.pop('username')
        super().save(*args, **kwargs)

    @staticmethod
    def createRuleClassifier(text_dict, experiment_classifier):
        model_name = text_dict['model_name']
        property_name = text_dict['property_name']
        property_value = text_dict['property_value']
        return RuleClassifier(experiment_classifier=experiment_classifier, model_name=model_name,
                              property_name=property_name, property_value=property_value)


class MappingClassifier(models.Model):
    x_exp_name = models.CharField(max_length=100)
    x_exp_location = models.CharField(max_length=100)
    x_sim_name = models.CharField(max_length=100)
    x_sim_location = models.CharField(max_length=100)

    y_exp_name = models.CharField(max_length=100)
    y_exp_location = models.CharField(max_length=100)
    y_sim_name = models.CharField(max_length=100)
    y_sim_location = models.CharField(max_length=100)

    file = models.CharField(max_length=100)

    experiment_classifier = models.ForeignKey(ExperimentClassifier, on_delete=models.CASCADE, related_name="mappings")

    def save(self, *args, **kwargs):
        if 'username' in kwargs:
            kwargs.pop('username')
        super().save(*args, **kwargs)

    @staticmethod
    def createMappingClassifier(text_dict, experiment_classifier):
        x_exp_name = text_dict['x_exp_name']
        x_exp_location = text_dict['x_exp_location']
        x_sim_name = text_dict['x_sim_name']
        x_sim_location = text_dict['x_sim_location']

        y_exp_name = text_dict['y_exp_name']
        y_exp_location = text_dict['y_exp_location']
        y_sim_name = text_dict['y_sim_name']
        y_sim_location = text_dict['y_sim_location']

        file = text_dict['file']

        return MappingClassifier(experiment_classifier=experiment_classifier, file=file,
                                 x_exp_name=x_exp_name, x_exp_location=x_exp_location,
                                 x_sim_name=x_sim_name, x_sim_location=x_sim_location,
                                 y_exp_name=y_exp_name, y_exp_location=y_exp_location,
                                 y_sim_name=y_sim_name, y_sim_location=y_sim_location)
