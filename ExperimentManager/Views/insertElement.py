# Local import
import ExperimentManager.views as View
from ExperimentManager.Models import *
from ExperimentManager.exceptions import *
from ReSpecTh.OptimaPP import TranslatorOptimaPP, OptimaPP
from ReSpecTh.zenodo import *
from ExperimentManager.checkExperiment import checkExperiment

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from django.db import transaction, DatabaseError

import json
import random


class insertElement(View.ExperimentManagerBaseView):
    viewName = 'insertElement'
    paramsType = {'model_name': str, 'property_dict': str}
    required_groups = {'POST': ['WRITE']}

    def view_post(self, request):
        username = request.user.username
        # username = 'pippo'

        supported_models = ['ExperimentInterpreter', 'ChemModel', 'Experiment', 'Species', 'FilePaper']

        self.property_dict = json.loads(self.property_dict)

        if self.model_name not in supported_models:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data=self.viewName + ": Model '{}' not supported yet.".format(self.model_name))

        try:
            model = eval(self.model_name)
        except NameError:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data=self.viewName + ": NameError. Model '{}' not exist.".format(self.model_name))
        try:
            with transaction.atomic():
                try:
                    if self.model_name == 'Experiment':
                        self.property_dict['fileDOI'] = 'tmp_' + str(random.randint(0, int(1e20)))
                        self.property_dict['username'] = username

                    list_objects = getattr(model, 'create' + self.model_name)(self.property_dict)

                except (MandatoryFieldError, ConstraintFieldExperimentError) as e:
                    return Response(self.viewName + ": " + str(e), status=HTTP_400_BAD_REQUEST)

                current_exp = None
                for obj in list_objects:
                    # In teoria il save lo si potrebbe portare dentro...farlo due volto non guasta
                    if isinstance(obj, Experiment):
                        # obj.username = username
                        obj.save()
                        current_exp = obj
                    else:
                        obj.save()

                if current_exp is not None:
                    checkExperiment(current_exp)
                    # raise ValueError('EDOOO')

        except (ExperimentConsistencyError, ConstraintFieldExperimentError, ChemModelError) as e:
            return Response(self.viewName + ": " + str(e), status=HTTP_400_BAD_REQUEST)
        except DatabaseError as e:
            print(e)
            return Response(self.viewName + ": " + str(e.__cause__), status=HTTP_400_BAD_REQUEST)

        return Response("{} element inserted successfully.".format(self.model_name), status=HTTP_200_OK)
