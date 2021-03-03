# Local import
import ExperimentManager.views as View
from ExperimentManager.Models import *

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from django.core.exceptions import ObjectDoesNotExist

import json


class updateElement(View.ExperimentManagerBaseView):
    viewName = 'updateElement'
    paramsType = {'model_name': str, 'element_id': int, 'property_dict': str}
    required_groups = {'POST': ['READ']}

    def view_post(self, request):
        self.property_dict = json.loads(self.property_dict)
        if self.model_name == 'Experiment' and 'status' in self.property_dict:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data="updateElement: It is not possible to verify and experiment.")
        try:
            model = eval(self.model_name)
        except NameError:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data="updateElement: NameError. Model '{}' not exist.".format(self.model_name))

        try:
            element = model.objects.get(pk=self.element_id)
            for prop in self.property_dict:
                if prop in element.__dict__:
                    setattr(element, prop, self.property_dict[prop])
                else:
                    return Response(status=HTTP_400_BAD_REQUEST,
                                    data="updateElement: Attribute '{}' not exist in model '{}'".format(prop,
                                                                                                        self.model_name))
            element.save()
        except ObjectDoesNotExist:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data="updateElement: ID Error. Element ID '{}' in Model '{}' not exist."
                            .format(self.element_id, self.model_name))

        # logger.info('Update Element ID {element_id} in Model {model_name}')
        return Response("{} element updated successfully.".format(self.model_name), status=HTTP_200_OK)
