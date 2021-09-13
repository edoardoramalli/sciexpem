from django.db import models
from ExperimentManager.exceptions import *
from django.contrib.postgres.fields import ArrayField
from django.conf import settings
import xml.etree.ElementTree as ET
import os


class ChemModel(models.Model):  # TODO Fuel list
    # Mandatory
    name = models.CharField(max_length=100, unique=True)
    xml_file_kinetics = models.TextField()
    xml_file_reaction_names = models.TextField()
    supported_species = ArrayField(models.CharField(max_length=20), null=True, blank=True)

    # Optional
    version = models.CharField(max_length=200, default='OTHERS')

    def save(self, *args, **kwargs):
        self.check_fields()
        tree = ET.ElementTree(ET.fromstring(self.xml_file_kinetics))
        root = tree.getroot()
        NamesOfSpecies = list(set(root.find('NamesOfSpecies').text.strip().split()))
        self.supported_species = NamesOfSpecies
        super().save(*args, **kwargs)

    def check_fields(self):
        versions = []
        with open(os.path.join(settings.BASE_DIR, "Files/model_version"), "r") as file:
            for line in file:
                versions.append(line.strip())

        if self.version not in versions:
            raise ChemModelError("Version is not valid.")

    @staticmethod
    def createChemModel(text_dict):
        # Mandatory
        try:
            name = text_dict['name']
            xml_file_kinetics = text_dict['xml_file_kinetics']
            xml_file_reaction_names = text_dict['xml_file_reaction_names']
            version = text_dict['version']
        except KeyError as error:
            raise MandatoryFieldError(error)

        model = ChemModel(name=name, version=version,
                          xml_file_kinetics=xml_file_kinetics, xml_file_reaction_names=xml_file_reaction_names)
        return [model]
