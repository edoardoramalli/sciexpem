# Local import
import ExperimentManager.views as View
from ExperimentManager.Models import *
from ExperimentManager.exceptions import *
from CurveMatching.CurveMatching import curveMatchingExecution
from OpenSmoke.OpenSmoke import getColumnNameSimulator
from django.db.models import Q
from SciExpeM.settings import SCIEXPEM_FILESYSTEM_FOLDER

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from django.db import transaction
from django.contrib.auth.models import User
from django.http import FileResponse

import pandas as pd

import json
import hashlib
import os

from SciExpeM import settings
from OpenSmoke.PostProcessor.pyPostProcessor.pyPostProcessor import compute_ropa

from OpenSmoke.utils import getMapIndexReactionName


class getROPA(View.ExperimentManagerBaseView):
    viewName = __name__
    paramsType = {'execution_id': int,
                  'specie_id': int,
                  'ROPA_type': int,
                  'local_value': float,
                  'lower_bound': float,
                  'upper_bound': float,
                  'case': int,
                  'n_reaction': int}
    defaultParams = {'local_value': 0.0, 'lower_bound': 0.0, 'upper_bound': 0.0, 'case': -1, 'n_reaction': 10}
    required_groups = {'POST': []}

    def view_post(self, request):

        execution = Execution.objects.get(id=self.execution_id)

        local_value = self.local_value if self.local_value is not None else 0.0
        lower_bound = self.lower_bound if self.lower_bound is not None else 0.0
        upper_bound = self.upper_bound if self.upper_bound is not None else 0.0


        # TODO solo se case == -1 allora facciamo tutti altrimeni solo quel case o i case

        execution_files = execution.execution_files.all()

        if len(execution_files) == 0:
            return Response({'ROPA': {}, 'reactions_map': {}}, status=HTTP_200_OK)

        specie = Species.objects.get(id=self.specie_id)

        ropa = {}

        reactions_used = set([])

        for ef in execution_files:
            coeff, react_index = compute_ropa(kineticFolder=execution.chemModel.absolute_folder_xml_file_kinetics_path,
                                              outputFolder=ef.absolute_folder_path,
                                              specie=specie.preferredKey,
                                              ROPA_type=self.ROPA_type,
                                              local_value=local_value,
                                              lower_bound=lower_bound,
                                              upper_bound=upper_bound, n_reaction=self.n_reaction)

            reactions_used.update(react_index)

            ropa[ef.case] = {'coefficients': coeff, 'reaction_index': react_index}

        current_map = getMapIndexReactionName(reaction_file_path=execution.chemModel.absolute_xml_file_reaction_names_path)

        sub_setmap = {index: current_map[index] for index in current_map if index in reactions_used}


        return Response({'ROPA': ropa, 'reactions_map': sub_setmap},status=HTTP_200_OK)
