from django.db import models
from SciExpeM import settings


class GeneralManager(models.Manager):

    def filter(self, *args, **kwargs):
        user = kwargs.pop('user')
        if not settings.DEBUG and user is None:
            raise ValueError('Query Manager User not specified!')
