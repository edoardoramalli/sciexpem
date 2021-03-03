from django.db import models
import ExperimentManager.Models as Model
from ExperimentManager.exceptions import *


class ExperimentInterpreter(models.Model):
    name = models.CharField(max_length=100, unique=True)
    model_type = models.CharField(max_length=100)  # TODO da rimuovere non serve a nulla. Il modello lo riprendo dai fuel
    solver = models.CharField(max_length=100)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    @staticmethod
    def createExperimentInterpreter(text_dict):
        try:
            name = text_dict['name']
            model_type = text_dict['model_type']
            solver = text_dict['solver']
            experiment_interpreter = ExperimentInterpreter(name=name, model_type=model_type, solver=solver)

            mappings = text_dict['mappings']
            tmp1 = [Model.MappingInterpreter.createMappingInterpreter(mapping, experiment_interpreter) for mapping in mappings]

            rules = text_dict['rules']
            tmp2 = [Model.RuleInterpreter.createRuleInterpreter(rule, experiment_interpreter) for rule in rules]
        except KeyError as error:
            raise MandatoryFieldError(error)

        return [experiment_interpreter] + tmp1 + tmp2
