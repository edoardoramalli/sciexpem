import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciExpeM.settings")
django.setup()

from ExperimentManager.Models import *

## SPECIES

## 1 make preferredKey unique

# species = Specie.objects.all()
#
# used_keys = set([])
#
# for spec in species.order_by('id'):
#     c_preferred_key = spec.preferredKey
#     if c_preferred_key in used_keys:
#         spec.preferredKey = c_preferred_key + '_{}'.format(specie.id)
#         spec.save()
#     used_keys.add(spec.preferredKey)

# FUELS
exps = Experiment.objects.all()

# for exp in exps:
#     fuels = exp.fuels
#     if fuels:
#         for fuel in fuels:
#             c_spec = Specie.objects.filter(preferredKey=fuel)
#             if c_spec.exists():
#                 exp.fuels_object.add(c_spec[0])
#             else:
#                 exp.notes = exp.notes + ' Old Fuel {}'.format(fuel) if exp.notes else ' Old Fuel {}'.format(fuel)
#         try:
#             exp.save()
#         except Exception as e:
#             print(e)
#             print(exp.id)


for exp in exps:
    print(exp.id, exp.fuels_object.all())
    # break

