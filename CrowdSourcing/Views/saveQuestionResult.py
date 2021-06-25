import CrowdSourcing.views as View
import datetime

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
import ExperimentManager.Models as Model
from CrowdSourcing.models import *
from django.db import transaction, DatabaseError


class saveQuestionResult(View.CrowdSourcingBaseView):
    viewName = 'saveQuestionResult'
    paramsType = {'answer': dict, 'experiment_id': int}

    required_groups = {'POST': []}

    def view_post(self, request):

        username = request.user.username
        # username = 'root'

        with transaction.atomic():

            task = Task(username=username, experiment=Model.Experiment.objects.get(id=self.experiment_id))

            task.save()

            for singleAnswer in self.answer:
                a = Answer(task=task,
                           y_exp=Model.DataColumn.objects.get(id=singleAnswer),
                           best_models=self.answer[singleAnswer]['best_models'],
                           wrong_models=self.answer[singleAnswer]['wrong_models'],
                           noise_level=self.answer[singleAnswer]['noise_level'],
                           choices=self.answer[singleAnswer]['choices'])
                a.save()

            current_user = Participant.objects.get(username=username)
            current_user.done += [self.experiment_id]
            current_user.save()

        return Response(status=HTTP_200_OK)
