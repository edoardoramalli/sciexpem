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
from sklearn.cluster import *
import numpy as np
import pandas as pd
from statistics import stdev, variance, mean, median, StatisticsError


class getCluster(View.FrontEndBaseView):
    viewName = __name__
    paramsType = {'query': dict, 'subject': str}
    required_groups = {'POST': ['READ']}

    def view_post(self, request):

        def apply_funcs(fun, value_list):
            try:
                return round(fun(value_list), 3)
            except (StatisticsError, ValueError):
                return None

        new = {'execution_column__execution__experiment__status': 'verified', **self.query}

        l = []

        for cm in Models.CurveMatchingResult.objects.filter(**new).distinct():
            value = float(getattr(cm, self.subject))
            exp = cm.execution_column.execution.experiment
            t_inf = float(exp.t_inf)
            t_sup = float(exp.t_sup)
            p_inf = float(exp.p_inf)
            p_sup = float(exp.p_sup)
            phi_inf = float(exp.phi_inf)
            phi_sup = float(exp.phi_sup)

            if value > 0:
                l.append({
                    'Exp': exp.id,
                    'T': (t_inf + t_sup) / 2,
                    'P': (p_inf + p_sup) / 2,
                    'phi': (phi_inf + phi_sup) / 2,
                    'value': value
                })

            # domain.add_value_range(x_range=(t_inf, t_sup), y_range=(p_inf, p_sup), z_range=(phi_inf, phi_sup),
            #                        value=value)

        df = pd.DataFrame(l)

        X = df[['T', 'P', 'phi', 'value']].to_numpy()

        # model = AffinityPropagation(damping=0.9)
        model = AffinityPropagation(damping=0.8)
        # fit the model
        model.fit(X)
        # assign a cluster to each example
        yhat = model.predict(X)
        # yhat = model.fit_predict(X)

        df['cluster'] = yhat

        funcs = [len, min, max, stdev, variance, mean, median]

        result = []

        def extract_info(df_):
            t_inf = min(sub_df['T'])
            t_sup = max(sub_df['T'])
            p_inf = min(sub_df['P'])
            p_sup = max(sub_df['P'])
            phi_inf = min(sub_df['phi'])
            phi_sup = max(sub_df['phi'])
            return {'T': (t_inf, t_sup), 'P': (p_inf, p_sup), 'phi': (phi_inf, phi_sup)}

        for cluster in np.unique(yhat):
            sub_df = df[df['cluster'] == cluster]
            result.append({'name': cluster,
                           'list': sub_df['Exp'],
                           **extract_info(sub_df),
                           **{fun.__name__: apply_funcs(fun, sub_df['value']) for fun in funcs}})

        return Response(result, status=HTTP_200_OK)
