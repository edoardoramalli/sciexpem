from django.db import models

import ExperimentManager.Models.Tool as Tool


class ChemModel(models.Model):  # TODO Fuel list
    # Mandatory
    name = models.CharField(max_length=100, unique=True)
    xml_file_kinetics = models.TextField()
    xml_file_reaction_names = models.TextField()

    # Optional
    version = models.CharField(max_length=200, null=True, blank=True)  # For which fuel it is

    def save(self, *args, **kwargs):
        kwargs['object'] = self
        Tool.generic_save(*args, **kwargs)

    @staticmethod
    def createChemModel(text_dict):
        # Mandatory
        name = text_dict['name']
        xml_file_kinetics = text_dict['xml_file_kinetics']
        xml_file_reaction_names = text_dict['xml_file_reaction_names']
        # Optional
        version = text_dict['version']

        model = ChemModel(name=name, version=version,
                          xml_file_kinetics=xml_file_kinetics, xml_file_reaction_names=xml_file_reaction_names)
        return [model]
