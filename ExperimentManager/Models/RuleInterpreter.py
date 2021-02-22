from django.db import models
import ExperimentManager.Models as Model


class RuleInterpreter(models.Model):
    model_name = models.CharField(max_length=100)
    property_name = models.CharField(max_length=100)
    property_value = models.CharField(max_length=100)
    experiment_interpreter = models.ForeignKey(Model.ExperimentInterpreter, on_delete=models.CASCADE,
                                               related_name="rules")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    @staticmethod
    def createRuleInterpreter(text_dict, experiment_interpreter):
        model_name = text_dict['model_name']
        property_name = text_dict['property_name']
        property_value = text_dict['property_value']
        return RuleInterpreter(experiment_interpreter=experiment_interpreter, model_name=model_name,
                               property_name=property_name, property_value=property_value)
