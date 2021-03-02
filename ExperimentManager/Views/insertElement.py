# Local import
import ExperimentManager.views as View
from ExperimentManager.Models import *
from ExperimentManager.exceptions import *
from ReSpecTh.OptimaPP import TranslatorOptimaPP, OptimaPP

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from django.db import transaction, DatabaseError

import json


class insertElement(View.ExperimentManagerBaseView):
    viewName = 'insertElement'
    paramsType = {'model_name': str, 'property_dict': str}
    required_groups = {'POST': ['WRITE']}

    def view_post(self, request):
        username = request.user.username

        supported_models = ['ExperimentInterpreter', 'ChemModel', 'Experiment']

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
                list_objects = getattr(model, 'create' + self.model_name)(self.property_dict)
                exp = None
                for obj in list_objects:
                    if isinstance(obj, Experiment):
                        obj.username = username
                        obj.save()
                        exp = obj
                    else:
                        obj.save()
                if exp is not None:
                    txt = TranslatorOptimaPP.create_OptimaPP_txt(experiment=exp,
                                                                 data_groups=exp.data_columns.all(),
                                                                 initial_species=exp.initial_species.all(),
                                                                 common_properties=exp.common_properties.all(),
                                                                 file_paper=exp.file_paper)
                    xml, error = OptimaPP.txt_to_xml(txt)
                    if error:
                        raise OptimaPPError(error)
                    else:
                        exp.xml_file = xml
                        exp.save()

        except DatabaseError as e:
            return Response(self.viewName + ": " + str(e.__cause__), status=HTTP_400_BAD_REQUEST)
        except ConstraintFieldExperimentError as e:
            return Response(self.viewName + ": " + str(e), status=HTTP_400_BAD_REQUEST)
        except OptimaPPError as e:
            return Response(self.viewName + ": OptimaPP error. " + str(e),
                            status=HTTP_400_BAD_REQUEST)

        return Response("{} element inserted successfully.".format(self.model_name), status=HTTP_200_OK)