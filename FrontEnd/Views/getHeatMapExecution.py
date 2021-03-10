# Local import
import FrontEnd.views as View
import ExperimentManager.Models as Models
from CurveMatching import CurveMatching

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

# System import
import json
import pandas as pd


class getHeatMapExecution(View.FrontEndBaseView):
    viewName = 'getHeatMapExecution'
    paramsType = {'exp_list': list, 'chemModel_list': list}
    required_groups = {'POST': ['READ']}

    def view_post(self):
        if not self.exp_list:
            return Response('getHeatMapExecution. Select at least one experiment.', status=HTTP_400_BAD_REQUEST)
        self.exp_list = [int(x) for x in self.exp_list]
        self.chemModel_list = [int(x) for x in self.chemModel_list] if self.chemModel_list else None

        query = {
            'execution_column__execution__experiment__id__in': self.exp_list
        }
        if self.chemModel_list:
            query['execution_column__execution__chemModel__id__in'] = self.chemModel_list

        cm_results = CurveMatching.getCurveMatching(query)

        record = {}
        experiment_list = []

        for exp in cm_results:
            experiment_list.append(exp['fileDOI'])
            if exp['fileDOI'] not in record:
                record[exp['fileDOI']] = []
            for model in exp['models']:
                record[exp['fileDOI']].append({'chemModel': model['name'], 'score': float(model['score'])})

        data = []

        for exp in record:
            tmp = {}
            for execution in record[exp]:
                tmp[execution['chemModel']] = execution['score']
            data.append(tmp)

        df = pd.DataFrame.from_records(data, index=record.keys())
        df = df.where(pd.notnull(df), None)  # Transform NaN in None
        x = list(df.index)
        y = list(df.columns)
        z = [list(df[model]) for model in df.columns]

        return Response({'x': x, 'y': y, 'z': z}, HTTP_200_OK)
