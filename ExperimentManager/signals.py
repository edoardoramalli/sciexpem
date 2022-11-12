import os
from django.db.models.signals import pre_delete
from django.dispatch import receiver
import shutil
from ExperimentManager.Models import *


def _delete_file(path):
    if os.path.isfile(path):
        os.remove(path)


def _delete_folder(path):
    if os.path.isdir(path):
        shutil.rmtree(path)


# Se specifico il sendere nel decorator non funziona ...
@receiver(pre_delete)
def delete_file(sender, instance, *args, **kwargs):
    if sender == ExecutionFile:
        _delete_file(instance.absolute_file_path)
    elif sender == Execution:
        _delete_folder(instance.absolute_folder_path)
    elif sender == ChemModel:
        _delete_folder(instance.absolute_folder_xml_file_kinetics_path)
    elif sender == ExperimentBackUp:
        _delete_folder(instance.absolute_folder_path)
