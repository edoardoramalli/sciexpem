# Local import
import ExperimentManager.views as View
from ExperimentManager.Models import *

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

import json
from decimal import Decimal


class requestProperty(View.ExperimentManagerBaseView):
    viewName = 'requestProperty'
    paramsType = {'model_name': str, 'element_id': int, 'property_name': str}
    required_groups = {'POST': ['READ']}

    def view_post(self, request):

        try:
            model = eval(self.model_name)
        except NameError:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data=self.viewName + ": NameError. Model '{}' not exist.".format(self.model_name))

        try:
            element = model.objects.get(id=self.element_id)
            property_object = getattr(element, self.property_name)
            property_object_type = type(property_object)

            if property_object is None:
                return Response('', status=HTTP_200_OK)
            elif property_object is []:
                return Response('', status=HTTP_200_OK)
            elif property_object_type is str:
                return Response(property_object, status=HTTP_200_OK)
            elif property_object_type is Decimal:
                return Response(property_object, status=HTTP_200_OK)
            elif property_object_type is int:
                return Response(property_object, status=HTTP_200_OK)
            elif property_object_type is bool:
                return Response(property_object, status=HTTP_200_OK)
            elif property_object_type is list:
                test = property_object[0]
                if type(test) is Decimal:
                    return Response(json.dumps([float(x) for x in property_object]), status=HTTP_200_OK)
                elif type(test) is str:
                    return Response(json.dumps([str(x) for x in property_object]), status=HTTP_200_OK)
                else:
                    return Response(status=HTTP_400_BAD_REQUEST,
                                    data=self.viewName + ": Data type List not supported.")
            else:
                return Response(status=HTTP_400_BAD_REQUEST,
                                data=self.viewName + ": Data type not supported.")
        except AttributeError:
            return Response(
                self.viewName + ": AttributeError. Property '{}' not exist for model '{}'.".format(self.property_name,
                                                                                                   self.model_name),
                status=HTTP_400_BAD_REQUEST)
