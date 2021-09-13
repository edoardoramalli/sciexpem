from django.db import models
from django.urls import reverse
from ExperimentManager.exceptions import *
import ExperimentManager.Models.Tool as Tool


class FilePaper(models.Model):
    # Mandatory
    description = models.CharField(max_length=500)

    # Optional
    reference_doi = models.CharField(max_length=100, unique=True, blank=True, null=True)  # DOI paper
    author = models.TextField(blank=True, null=True)
    title = models.TextField(blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)   # Checked
    volume = models.CharField(max_length=50, blank=True, null=True)
    page = models.CharField(max_length=50, blank=True, null=True)
    journal = models.TextField(blank=True, null=True)

    # TODO se inserisco un esperimento con un DOI di un paper già esistente non deve arrabbiarsi ma solo linkarlo
    # TODO nel caso in cui venga creato da form viene fatto, da file non so

    def get_absolute_url(self):
        return reverse('filepaper', kwargs={'pk': self.pk})

    @staticmethod
    def createFilePaper(text_dict):
        # Mandatory
        description = text_dict['description']
        # Optional
        author = text_dict.get('author')
        title = text_dict.get('title')
        volume = text_dict.get('volume')
        page = text_dict.get('page')
        journal = text_dict.get('journal')

        reference_doi = text_dict.get('reference_doi')
        query = FilePaper.objects.filter(reference_doi=reference_doi)
        if query.exists():
            return query[0]
        else:
            return FilePaper(description=description,
                             author=author,
                             title=title,
                             volume=volume,
                             page=page,
                             journal=journal,
                             reference_doi=reference_doi)

    def check_fields(self):
        reference_doi = self.reference_doi
        year = self.year

        if reference_doi and not reference_doi.startswith("10."):
            raise ConstraintFieldExperimentError("DOI {} is not valid.".format(reference_doi))

        if year and not 1900 < year < 2030:
            raise ConstraintFieldExperimentError("Year {} is not valid. 1900 < year < 2030".format(year))

    def save(self, *args, **kwargs):
        self.check_fields()
        super().save(*args, **kwargs)
