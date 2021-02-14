from django.db import models
from django.urls import reverse

import ExperimentManager.Models.Tool as Tool


class FilePaper(models.Model):
    # Mandatory
    references = models.CharField(max_length=500)

    # Optional
    reference_doi = models.CharField(max_length=100, unique=True, blank=True, null=True)  # DOI paper

    # TODO se inserisco un esperimento con un DOI di un paper già esistente non deve arrabbiarsi ma solo linkarlo
    # TODO nel caso in cui venga creato da form viene fatto, da file non so

    def get_absolute_url(self):
        return reverse('filepaper', kwargs={'pk': self.pk})

    @staticmethod
    def createFilePaper(text_dict):
        # Mandatory
        references = text_dict['references']
        # Optional
        reference_doi = text_dict.get('reference_doi')
        query = FilePaper.objects.filter(reference_doi=reference_doi)
        if query.exists():
            return query[0]
        else:
            return FilePaper(references=references, reference_doi=reference_doi)

    def save(self, *args, **kwargs):
        kwargs['object'] = self
        Tool.generic_save(*args, **kwargs)
