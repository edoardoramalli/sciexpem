# Local import
import ExperimentManager.views as View
import ExperimentManager.Serializers as Serializers
from ExperimentManager.Models import *
from ExperimentManager import QSerializer

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from django.core.exceptions import FieldError


def edo(x):
    try:
        return dict(x)
    except Exception:
        return str(x)


class filterDataBase(View.ExperimentManagerBaseView):
    """
    Scope  -> API to query all the models in the database. Used by BE.
    Param  -> model_name = a string with the name of the model to interrogate
    Param  -> query = a serialize django object Q. By default we use distinct() !
    Method -> POST
    Access -> READ Group
    """
    viewName = 'filterDataBase'
    paramsType = {'model_name': str, 'query': edo, 'fields': tuple}
    defaultParams = {'fields': []}
    required_groups = {'POST': ['READ']}

    def view_post(self, request):

        ser_fields = self.fields if self.fields else None

        try:
            model = eval(self.model_name)
        except NameError:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data=self.viewName + ": NameError. Model '{}' not exist.".format(self.model_name))

        q_serializer = QSerializer.QSerializer()
        query_obj = q_serializer.loads(self.query) if type(self.query) == str else self.query

        try:
            result = []
            if type(query_obj) == dict:
                query_set = model.objects.filter(**query_obj).distinct()
            else:
                query_set = model.objects.filter(query_obj).distinct()

            serializer = eval('Serializers.' + self.model_name + 'Serializer')
            for query_result in query_set:
                result.append(serializer(query_result, fields=ser_fields).data)



            return Response(result, status=HTTP_200_OK)
        except FieldError:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data=self.viewName + ": FieldError. Query '{}' is incorrect for model '{}'."
                            .format(self.query, self.model_name))

