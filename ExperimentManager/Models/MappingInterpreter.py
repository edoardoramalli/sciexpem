from django.db import models
import ExperimentManager.Models as Model


class MappingInterpreter(models.Model):
    x_exp_name = models.CharField(max_length=100)
    x_exp_location = models.CharField(max_length=100)
    x_sim_name = models.CharField(max_length=100)
    x_sim_location = models.CharField(max_length=100)
    x_transformation = models.CharField(max_length=15, default='lin')

    y_exp_name = models.CharField(max_length=100)
    y_exp_location = models.CharField(max_length=100)
    y_sim_name = models.CharField(max_length=100)
    y_sim_location = models.CharField(max_length=100)
    y_transformation = models.CharField(max_length=15, default='lin')

    file = models.CharField(max_length=100)

    experiment_interpreter = models.ForeignKey(Model.ExperimentInterpreter, on_delete=models.CASCADE,
                                               related_name="mappings")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    @staticmethod
    def createMappingInterpreter(text_dict, experiment_interpreter):
        x_exp_name = text_dict['x_exp_name']
        x_exp_location = text_dict['x_exp_location']
        x_sim_name = text_dict['x_sim_name']
        x_sim_location = text_dict['x_sim_location']
        x_transformation = text_dict['x_transformation']

        y_exp_name = text_dict['y_exp_name']
        y_exp_location = text_dict['y_exp_location']
        y_sim_name = text_dict['y_sim_name']
        y_sim_location = text_dict['y_sim_location']
        y_transformation = text_dict['y_transformation']

        file = text_dict['file']

        return MappingInterpreter(experiment_interpreter=experiment_interpreter, file=file,
                                  x_transformation=x_transformation, y_transformation=y_transformation,
                                  x_exp_name=x_exp_name, x_exp_location=x_exp_location,
                                  x_sim_name=x_sim_name, x_sim_location=x_sim_location,
                                  y_exp_name=y_exp_name, y_exp_location=y_exp_location,
                                  y_sim_name=y_sim_name, y_sim_location=y_sim_location)
