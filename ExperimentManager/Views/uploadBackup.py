# Local import
import ExperimentManager.views as View
import ExperimentManager.Serializers as Serializers
from ExperimentManager.Models import *
from ExperimentManager import QSerializer
from SciExpeM.settings import SCIEXPEM_FILESYSTEM_FOLDER


# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from django.core.exceptions import FieldError
import base64
import os


def custom_float_cast(val):
    if val is None:
        return None
    else:
        return float(val)


def custom_str_cast(val):
    if val is None:
        return None
    else:
        return str(val)

class uploadBackup(View.ExperimentManagerBaseView):
    """
    Scope  ->
    Param  ->
    Param  ->
    Method ->
    Access ->
    """

    viewName = 'uploadBackup'
    paramsType = {'experiment_id': int, 'chemModel_id': int, 'file_byte': str, 'file_name': str,
                  'parameter_name': custom_str_cast, 'parameter_unit': custom_str_cast, 'parameter_value': custom_float_cast}
    defaultParams = {'parameter_name': None, 'parameter_unit': None, 'parameter_value': None}
    required_groups = {'POST': ['WRITE']}

    def view_post(self, request):

        username = request.user.username
        # username = 'pippo'

        file_binary = base64.b64decode(self.file_byte)

        query = ExperimentBackUp.objects.filter(
            experiment__id=self.experiment_id,
            chemModel_id=self.chemModel_id,
            parameter_name=self.parameter_name,
            parameter_unit=self.parameter_unit,
            parameter_value=self.parameter_value
        )

        if query.exists():
            return Response("This BackUp already exist!", status=HTTP_400_BAD_REQUEST)

        # TODO in teoria se è gia presente uno con "parameter" tutti a None e poi ne aggiungo uno con dei parameter dovrebbe arrabbiarsi...

        backup_obj = ExperimentBackUp(experiment=Experiment.objects.get(id=self.experiment_id),
                                      chemModel=ChemModel.objects.get(id=self.chemModel_id),
                                      parameter_name=self.parameter_name,
                                      parameter_unit=self.parameter_unit,
                                      parameter_value=self.parameter_value,
                                      username=username,
                                      path='tmp_path')
        backup_obj.save()

        relative_backup_path = os.path.join('BackUp', str(backup_obj.id))

        absolute_local_backup_path = os.path.join(SCIEXPEM_FILESYSTEM_FOLDER, relative_backup_path)

        os.makedirs(absolute_local_backup_path, exist_ok=True)

        file_path = os.path.join(absolute_local_backup_path, self.file_name)

        with open(file_path, 'wb') as file:
            file.write(file_binary)

        backup_obj.path = os.path.join(relative_backup_path, self.file_name)
        backup_obj.save()

        # print(self.file)
        return Response(status=HTTP_200_OK)


