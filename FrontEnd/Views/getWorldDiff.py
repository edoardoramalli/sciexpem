# Local import
import FrontEnd.views as View
import ExperimentManager.Models as Models
import ExperimentManager.Serializers as Serializers
from FrontEnd.Domain import Domain

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

# System import
import json
import numpy as np
from statistics import stdev, variance, mean, median, StatisticsError
from FrontEnd.utils import *

class getWorldDiff(View.FrontEndBaseView):
    viewName = __name__
    paramsType = {'query': dict, 'subject': str, 'modelA': int, 'modelB': int, 'common_experiments': bool}
    defaultParams = {'common_experiments': False}
    required_groups = {'POST': ['READ']}

    def view_post(self, request):
        domainA = Domain()
        domainB = Domain()

        def replaceValueDict(diz, old, new):
            tmp = {}
            for key in diz:
                if diz[key] == old:
                    tmp[key] = new
                else:
                    tmp[key] = diz[key]
            return tmp

        modelA = {'execution_column__execution__experiment__status': 'verified',
                  **replaceValueDict(self.query, '$$$', self.modelA)}
        modelB = {'execution_column__execution__experiment__status': 'verified',
                  **replaceValueDict(self.query, '$$$', self.modelB)}

        if self.common_experiments:
            commons =  common_execution_experiment_id(self.modelA, self.modelB)
            modelA = {**modelA, 'execution_column__execution__experiment__id__in': commons}
            modelB = {**modelB, 'execution_column__execution__experiment__id__in': commons}


        def process_query(query, domain):
            for cm in Models.CurveMatchingResult.objects.filter(**query).distinct():
                value = float(getattr(cm, self.subject))
                exp = cm.execution_column.execution.experiment
                t_inf = float(exp.t_inf)
                t_sup = float(exp.t_sup)
                p_inf = float(exp.p_inf)
                p_sup = float(exp.p_sup)
                phi_inf = float(exp.phi_inf)
                phi_sup = float(exp.phi_sup)

                domain.add_value_range(x_range=(t_inf, t_sup), y_range=(p_inf, p_sup), z_range=(phi_inf, phi_sup),
                                       value=value)

        process_query(modelA, domainA)
        process_query(modelB, domainB)


        # modelA_avg = domainA.matrix / domainA.support
        #
        # modelB_avg = domainB.matrix / domainB.support
        #
        # diff = modelA_avg - modelB_avg

        # print(diff)

        from itertools import product

        r_x = []
        r_y = []
        r_z = []
        r_c = []
        r_s = []

        for x, y, z in product(domainA.x, domainA.y, domainA.z):

            x_index = np.where(domainA.x == x)
            y_index = np.where(domainA.y == y)
            z_index = np.where(domainA.z == z)
            c_value_A = domainA.matrix[x_index, y_index, z_index][0][0]
            c_value_B = domainB.matrix[x_index, y_index, z_index][0][0]
            if c_value_A and c_value_A >= 0 and c_value_B and c_value_B >= 0:
                r_x.append(float(x))
                r_y.append(float(y))
                r_z.append(float(z))
                c_a = float(c_value_A / domainA.support[x_index, y_index, z_index][0][0])
                c_b = float(c_value_B / domainB.support[x_index, y_index, z_index][0][0])
                r_c.append(c_a - c_b)
                r_s.append(int((domainA.support[x_index, y_index, z_index][0][0] + domainB.support[x_index, y_index, z_index][0][0]) / 2))
                # print(c_value_A, c_value_B, c_a - c_b)

        result = {'x': r_x,
                  'y': r_y,
                  'z': r_z,
                  'c': r_c,
                  's': r_s}

        return Response(json.dumps(result), status=HTTP_200_OK)

        # return Response(json.dumps(final_final), status=HTTP_200_OK)
