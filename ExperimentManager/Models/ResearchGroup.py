from django.db import models


class ResearchGroup(models.Model):
    name = models.CharField(max_length=75, unique=True)

    def save(self, *args, **kwargs):
        self.check_fields()
        super().save(*args, **kwargs)

    def check_fields(self):
        pass