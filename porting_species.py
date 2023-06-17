import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciExpeM.settings")
django.setup()

from ExperimentManager.Models import *


# exp = Experiment.objects.filter(id=201)[0]
#
# print(exp.fuels_object.all())
#
# exit()

## SPECIES

## 1 make preferredKey unique

species = Species.objects.all()

used_keys = set([])

to_be_changed = []

for spec in species.order_by('id'):
    c_preferred_key = spec.preferredKey
    if c_preferred_key in used_keys:
        spec.preferredKey = c_preferred_key + '_{}'.format(spec.id)
        to_be_changed.append(spec.id)
        spec.save()
    used_keys.add(spec.preferredKey)

# FUELS
exps = Experiment.objects.all()

fuels_to_changed = []

for exp in exps:
    fuels = exp.fuels
    if fuels:
        for fuel in fuels:
            c_spec = Species.objects.filter(preferredKey=fuel)
            if c_spec.exists():
                exp.fuels_object.add(c_spec[0])
            else:
                exp.notes = exp.notes + ' Old Fuel {}'.format(fuel) if exp.notes else ' Old Fuel {}'.format(fuel)
                fuels_to_changed.append(exp.id)
        try:
            exp.save()
        except Exception as e:
            print(e)
            print(exp.id)

print('Species', to_be_changed)
print('Fuels', fuels_to_changed)



