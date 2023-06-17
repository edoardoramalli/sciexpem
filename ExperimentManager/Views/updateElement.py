# Local import
import ExperimentManager.views as View
from ExperimentManager.Models import *
from ExperimentManager.exceptions import *
from ExperimentManager.checkExperiment import checkExperiment


# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models.fields.related import ManyToManyField

import json


class updateElement(View.ExperimentManagerBaseView):
    viewName = 'updateElement'
    paramsType = {'model_name': str, 'element_id': int, 'property_dict': str}
    required_groups = {'POST': ['WRITE']}

    def view_post(self, request):
        self.property_dict = json.loads(self.property_dict)
        if not self.property_dict:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data="updateElement: property_dict is empty")
        if self.model_name == 'Experiment' and 'status' in self.property_dict:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data="updateElement: It is not possible to verify and experiment.")
        try:
            model = eval(self.model_name)
        except NameError:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data="updateElement: NameError. Model '{}' not exist.".format(self.model_name))

        try:
            with transaction.atomic():
                element = model.objects.select_for_update().get(pk=self.element_id)
                # TODO impedire modifica di alcuni attributi se ho già verificato --> generato doi
                # TODO se l'elemento modificato è un exp far partire di nuovo il check
                for prop in self.property_dict:
                    # print(element.__class__.__dict__)
                    # print(element.__dict__)
                    if prop in element.__class__.__dict__:
                        if type(getattr(getattr(model, '_meta'), 'get_field')(prop)) != ManyToManyField:
                            setattr(element, prop, self.property_dict[prop])
                        else:
                            getattr(element, prop).clear()
                            getattr(element, prop).add(*self.property_dict[prop])
                    else:
                        return Response(status=HTTP_400_BAD_REQUEST,
                                        data="updateElement: Attribute '{}' not exist in model '{}'".format(prop,
                                                                                                            self.model_name))
                element.save()
                if self.model_name == 'Experiment':
                    checkExperiment(element)
                    # TODO RIMETTERE RICALCOLO INTERPRETE DOPO UPDATE PARAMETRI!
                    # Cosi viene ricalcolato se cambio qualche parametro
                    # element.experiment_interpreter = None
                    # # Questa istruzione forza a ricalcolarlo
                    # tmp = element.interpreter
                    element.save()

        except (ExperimentConsistencyError, ConstraintFieldExperimentError, ChemModelError, SpecieConsistencyError) as e:
            return Response(self.viewName + ": " + str(e), status=HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data="updateElement: ID Error. Element ID '{}' in Model '{}' not exist."
                            .format(self.element_id, self.model_name))

        # logger.info('Update Element ID {element_id} in Model {model_name}')
        return Response("{} element updated successfully.".format(self.model_name), status=HTTP_200_OK)
