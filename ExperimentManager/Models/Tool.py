from ExperimentManager.exceptions import *
from django.utils import timezone
import ExperimentManager.Models as Model

MAX_DIGITS = 42
DECIMAL_PLACES = 10


# def generic_save(*args, **kwargs):
#     if 'username' in kwargs and 'object' in kwargs:
#         username = kwargs.pop('username')
#         obj = kwargs.pop('object')
#         super(obj.__class__, obj).save(*args, **kwargs)
#         log = model.LoggerModel(model_name=obj.__class__.__name__,
#                                 pk_model=obj.pk,
#                                 username=username,
#                                 action="save",
#                                 date=timezone.now())
#         log.save()
#     else:
#         raise ConstraintFieldExperimentError("Username field not specified!")


# def generic_delete(*args, **kwargs):
#     if 'username' in kwargs and 'object' in kwargs:
#         username = kwargs.pop('username')
#         obj = kwargs.pop('object')
#         super(obj.__class__, obj).delete(*args, **kwargs)
#         log = Model.LoggerModel(model_name=obj.__class__.__name__,
#                                 pk_model=obj.pk,
#                                 username=username,
#                                 action="delete",
#                                 date=timezone.now())
#         log.save()
#     else:
#         raise ConstraintFieldExperimentError("Username field not specified!")
