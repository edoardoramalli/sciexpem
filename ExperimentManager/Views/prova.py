# Local import
import ExperimentManager.views as View
from ExperimentManager.Models import *
from ExperimentManager.exceptions import *
from OpenSmoke.OpenSmoke import getColumnNameSimulator

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from django.db import transaction
from django.contrib.auth.models import User


class prova(View.ExperimentManagerBaseView):
    viewName = 'prova'
    paramsType = {}
    # paramsType = {'status': str, 'exp_id': int}

    required_groups = {'POST': []}

    def view_post(self, request):
        users = []
        #
        # for user in User.objects.all():
        #     users.append({'username': user.username,
        #                   'first_name': user.first_name,
        #                   'last_name': user.last_name,
        #                   'email': user.email,
        #                   'is_staff': user.is_staff,
        #                   'groups': [group for group in list(user.groups.values_list('name', flat=True))]})


        exp = Experiment.objects.get(id=1459)
        print(exp.id)
        getColumnNameSimulator(exp)

        print(exp.interpreter, exp.id)

        return Response(status=HTTP_200_OK, data=users)
