from django.db import models
import ExperimentManager.Models as Model
import os
from SciExpeM.settings import SCIEXPEM_FILESYSTEM_FOLDER


class ExecutionFile(models.Model):
    case = models.IntegerField(null=True, blank=True)
    path = models.TextField()
    type = models.CharField(max_length=50)
    specie = models.ForeignKey(Model.Species, on_delete=models.SET_NULL, default=None, null=True)
    execution = models.ForeignKey(Model.Execution, on_delete=models.CASCADE, related_name="execution_files")

    # CHECK on_delete policy !!!

    class Meta:
        unique_together = ('id', 'case',)

    def save(self, *args, **kwargs):
        self.check_fields()
        super().save(*args, **kwargs)

    @property
    def file(self):
        with open(self.path, 'r') as file:
            return file.read()

    @property
    def absolute_folder_path(self):
        return os.path.dirname(os.path.join(SCIEXPEM_FILESYSTEM_FOLDER, self.path))

    @property
    def absolute_file_path(self):
        return os.path.join(SCIEXPEM_FILESYSTEM_FOLDER, self.path)

    def check_fields(self):
        pass


