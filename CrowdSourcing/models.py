from django.db import models
from django.contrib.postgres.fields import ArrayField
from ExperimentManager.exceptions import *
import ExperimentManager.Models.Tool as Tool
import ExperimentManager.Models as Model
from django.conf import settings
import os


class Participant(models.Model):
    username = models.CharField(max_length=100, unique=True)
    done = ArrayField(models.IntegerField(), default=None)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class Task(models.Model):
    # Mandatory
    date = models.TimeField(auto_now=True)
    username = models.CharField(max_length=100)
    experiment = models.ForeignKey(Model.Experiment, on_delete=models.CASCADE, related_name="tasks")


class Answer(models.Model):
    # Mandatory
    choices = ArrayField(models.IntegerField())     # Model.ExecutionColumn
    y_exp = models.ForeignKey(Model.DataColumn, on_delete=models.CASCADE, related_name="y_exp")
    best_models = ArrayField(models.IntegerField())     #ArrayField(Model.ExecutionColumn)
    wrong_models = ArrayField(models.IntegerField())    #ArrayField(Model.ExecutionColumn)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="answers")
    noise_level = models.IntegerField()
