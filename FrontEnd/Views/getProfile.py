# Local import
import FrontEnd.views as View

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

# System import
import json


class getProfile(View.FrontEndBaseView):
    viewName = 'getProfile'
    paramsType = {'data': str}
    required_groups = {'POST': ['WRITE']}

    def view_post(self, request):
        text = self.data.split('\n')
        first_column_name = text[0].strip().split(';')[0]
        first_column_unit = text[0].strip().split(';')[1]

        second_column_name = text[1].strip().split(';')[0]
        second_column_unit = text[1].strip().split(';')[1]

        first_data = []
        second_data = []
        for line in text[2:]:
            if not line:
                break
            split_line = line.strip().split(';')
            first_data.append(float(split_line[0]))
            second_data.append(float(split_line[1]))

        result = [{'name': first_column_name, 'units': first_column_unit, 'data': first_data},
                  {'name': second_column_name, 'units': second_column_unit, 'data': second_data}]

        return Response(result, status=HTTP_200_OK)
