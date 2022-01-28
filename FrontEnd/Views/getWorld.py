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



class getWorld(View.FrontEndBaseView):
    viewName = __name__
    paramsType = {'query': dict, 'subject': str}
    required_groups = {'POST': ['READ']}

    def view_post(self, request):
        domain = Domain()

        new = {'execution_column__execution__experiment__status': 'verified', **self.query}

        for cm in Models.CurveMatchingResult.objects.filter(**new).distinct():
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

        from itertools import product

        r_x = []
        r_y = []
        r_z = []
        r_c = []
        r_s = []

        for x, y, z in product(domain.x, domain.y, domain.z):

            x_index = np.where(domain.x == x)
            y_index = np.where(domain.y == y)
            z_index = np.where(domain.z == z)
            c_value = domain.matrix[x_index, y_index, z_index][0][0]
            if c_value and c_value >= 0:
                r_x.append(float(x))
                r_y.append(float(y))
                r_z.append(float(z))
                r_c.append(float(c_value / domain.support[x_index, y_index, z_index][0][0]))
                r_s.append(float(domain.support[x_index, y_index, z_index][0][0]))

        result = {'x': r_x,
                  'y': r_y,
                  'z': r_z,
                  'c': r_c,
                  's': r_s}

        return Response(json.dumps(result), status=HTTP_200_OK)

        # return Response(json.dumps(final_final), status=HTTP_200_OK)
