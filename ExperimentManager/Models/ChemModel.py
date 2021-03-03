from django.db import models
from ExperimentManager.exceptions import *


class ChemModel(models.Model):  # TODO Fuel list
    # Mandatory
    name = models.CharField(max_length=100, unique=True)
    xml_file_kinetics = models.TextField()
    xml_file_reaction_names = models.TextField()

    # Optional
    version = models.CharField(max_length=200, null=True, blank=True)  # For which fuel it is

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    @staticmethod
    def createChemModel(text_dict):
        # Mandatory
        try:
            name = text_dict['name']
            xml_file_kinetics = text_dict['xml_file_kinetics']
            xml_file_reaction_names = text_dict['xml_file_reaction_names']
        except KeyError as error:
            raise MandatoryFieldError(error)

        # Optional
        version = text_dict.get('version')

        model = ChemModel(name=name, version=version,
                          xml_file_kinetics=xml_file_kinetics, xml_file_reaction_names=xml_file_reaction_names)
        return [model]
