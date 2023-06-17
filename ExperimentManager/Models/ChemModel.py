from django.db import models
from ExperimentManager.exceptions import *
from django.contrib.postgres.fields import ArrayField
from django.conf import settings
from ExperimentManager.Models import Species
from SciExpeM.settings import BASE_DIR
import xml.etree.ElementTree as ET
import os
import tempfile
from SciExpeM.settings import SCIEXPEM_FILESYSTEM_FOLDER


class ChemModel(models.Model):  # TODO Fuel list
    # TODO implementare delete che cancella folder
    # Mandatory
    name = models.CharField(max_length=100, unique=True)
    xml_file_kinetics = models.TextField()
    xml_file_reaction_names = models.TextField()
    supported_species = ArrayField(models.CharField(max_length=20), null=True, blank=True)

    # Optional
    version = models.CharField(max_length=200, default='OTHERS')


    @property
    def absolute_xml_file_kinetics_path(self):
        return os.path.join(SCIEXPEM_FILESYSTEM_FOLDER, self.xml_file_kinetics)

    @property
    def absolute_xml_file_reaction_names_path(self):
        return os.path.join(SCIEXPEM_FILESYSTEM_FOLDER, self.xml_file_reaction_names)

    @property
    def absolute_folder_xml_file_reaction_names_path(self):
        return os.path.dirname(self.absolute_xml_file_reaction_names_path)

    @property
    def absolute_folder_xml_file_kinetics_path(self):
        return os.path.dirname(self.absolute_xml_file_kinetics_path)

    @property
    def xml_file_kinetics_file(self):
        with open(self.absolute_xml_file_kinetics_path, 'r') as file:
            return file.read()

    @property
    def xml_file_reaction_names_file(self):
        with open(self.absolute_xml_file_reaction_names_path, 'r') as file:
            return file.read()

    @xml_file_kinetics_file.setter
    def xml_file_kinetics_file(self, value):
        with open(self.absolute_xml_file_kinetics_path, 'w+') as file:
            file.write(value)

    @xml_file_reaction_names_file.setter
    def xml_file_reaction_names_file(self, value):
        with open(self.absolute_xml_file_reaction_names_path, 'w+') as file:
            file.write(value)

    @property
    def mapping_id_name_supported_species(self):
        r = {}
        for s in self.supported_species:
            try:
                c_s = Species.objects.get(preferredKey=s)
                r[c_s.id] = s
            except Exception:
                # TODO CHE FARE SE NON LA TROVA?
                pass
        return r

    def save(self, *args, **kwargs):
        self.check_fields()

        super().save(*args, **kwargs)

    def create_supported_species(self):
        tree = ET.ElementTree(ET.fromstring(self.xml_file_kinetics_file))
        root = tree.getroot()
        NamesOfSpecies = list(set(root.find('NamesOfSpecies').text.strip().split()))
        self.supported_species = NamesOfSpecies
        self.save()

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

            xml_file_kinetics_file = text_dict['xml_file_kinetics']
            xml_file_reaction_names_file = text_dict['xml_file_reaction_names']

            version = text_dict['version']

            with tempfile.TemporaryDirectory() as tmp_dir:
                kinetics_path = os.path.join(tmp_dir, 'kinetics.xml')
                reaction_names_path = os.path.join(tmp_dir, 'reaction_names.xml')

                with open(kinetics_path, 'w+') as file:
                    file.write(xml_file_kinetics_file)

                with open(reaction_names_path, 'w+') as file:
                    file.write(xml_file_reaction_names_file)

                model = ChemModel(name=name, version=version,
                                  xml_file_kinetics=kinetics_path, xml_file_reaction_names=reaction_names_path)

                model.save()

                relative_path = os.path.join('ChemModel', str(model.id))

                absolute_model_path = os.path.join(SCIEXPEM_FILESYSTEM_FOLDER, relative_path)



                os.makedirs(absolute_model_path, exist_ok=True)

                new_kinetics_path = os.path.join(absolute_model_path, 'kinetics.xml')
                new_reaction_names_path = os.path.join(absolute_model_path, 'reaction_names.xml')

                os.rename(kinetics_path, new_kinetics_path)
                os.rename(reaction_names_path, new_reaction_names_path)

                model.xml_file_kinetics = os.path.join(relative_path, 'kinetics.xml')
                model.xml_file_reaction_names = os.path.join(relative_path, 'reaction_names.xml')
                model.save()
                model.create_supported_species()

                return [model]


        except KeyError as error:
            raise MandatoryFieldError(error)



