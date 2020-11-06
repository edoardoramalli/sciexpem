from django.core.management.base import BaseCommand
from django.utils import timezone
import numpy as np
from experimentmanager import models

from django.db.models import Count, Q

from experimentmanager import opensmoke

from experimentmanager.IOReSpecThOS import IOReSpecThOS


class Command(BaseCommand):
    help = 'Execute curve matching for experiment with simulation, ' \
           'should be possibile to re-execute it without side-effects'

    # (Q(data_columns__name="temperature") | Q(data_columns__name="ignition delay"))). \

    def handle(self, *args, **kwargs):
        # ---> Case 0: IDT - Shock Tube - T,tau
        experiment_type = "ignition delay measurement"
        reactor = "shock tube"
        data_group_fields = ["T", "tau"]
        exp = models.Experiment.objects. \
            filter(Q(experiment_type=experiment_type) &
                   Q(reactor=reactor)). \
            annotate(num_data=Count("data_columns")). \
            filter(Q(num_data=2))

        exp = exp.filter(Q(data_columns__name="temperature"))
        exp = exp.filter(Q(data_columns__name="ignition delay"))

        output_file, output_fields = IOReSpecThOS.query(experiment_type=experiment_type,
                                                        reactor=reactor,
                                                        data_group_fields=data_group_fields)

        for e in exp:
            print(e.fileDOI)

    # for t in target:
    #     if not t.common_properties.filter(name="pressure") and t.data_columns.filter(name="pressure"):
    #         pressure_column = t.data_columns.get(name="pressure")
    #         average_pressure = np.mean(pressure_column.data)
    #         cp = models.CommonProperty(experiment=t, name="pressure", units=pressure_column.units,
    #                                    value=average_pressure, sourcetype="ts_average")
    #         cp.save()
    # target = models.Experiment.objects.filter(reactor="flow reactor")
    # for t in target:
    #     if not t.common_properties.filter(name="residence time") and t.data_columns.filter(
    #             name="residence time"):
    #         rt_column = t.data_columns.get(name="residence time")
    #         average_rt = np.mean(rt_column.data)
    #         cp = models.CommonProperty(experiment=t, name="residence time", units=rt_column.units,
    #                                    value=average_rt, sourcetype="ts_average")
    #         cp.save()
    #
    # # rename: common equivalence ratio -> phi
    # target = models.Experiment.objects.all()
    # for t in target:
    #     if not t.common_properties.filter(name="phi") and t.common_properties.filter(name='equivalence ratio'):
    #         eq_property = t.common_properties.get(name='equivalence ratio')
    #
    #         phi_property = models.CommonProperty(experiment=t, name="phi", units="unitless",
    #                                              value=eq_property.value, sourcetype="ts_rename")
    #         phi_property.save()
