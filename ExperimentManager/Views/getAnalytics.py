# Local import
import ExperimentManager.views as View
from ExperimentManager.Models import *
from CurveMatching import CurveMatching

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from django.db.models import Q


class getAnalytics(View.ExperimentManagerBaseView):
    """
    Used by: UI -> {ExperimentTable: CurveMatching Raw Data, CurveMatching Bar Plot}
    Used by: API
    """
    viewName = 'getAnalytics'
    paramsType = {}
    required_groups = {'POST': ['READ']}

    def view_post(self, request):
        result = {}

        # Experiment

        exp_total = Experiment.objects.all().count()
        exp_verified = Experiment.objects.filter(status='verified').count()
        exp_unverified = Experiment.objects.filter(status='unverified').count()
        exp_invalid = Experiment.objects.filter(status='invalid').count()
        exp_managed = Experiment.objects.filter(~Q(experiment_interpreter=None)).count()

        result['experiment']['total'] = exp_total
        result['experiment']['status'] = {
            'verified': exp_verified,
            'unverified': exp_unverified,
            'invalid': exp_invalid, }
        result['experiment']['managed'] = {'managed': exp_managed}

        # Get reactors

        result['experiment']['reactor'] = {}

        for x in Experiment.objects.all().values('reactor').distinct():
            reactor = x['reactor']
            result['experiment']['reactor'][reactor] = Experiment.objects.filter(reactor=reactor).count()

        result['experiment']['experiment_type'] = {}

        # Exp type
        for x in Experiment.objects.all().values('experiment_type').distinct():
            experiment_type = x['experiment_type']
            result['experiment']['experiment_type'][experiment_type] = Experiment.objects.filter(experiment_type=experiment_type).count()

        result['experiment'] = {'total': Execution.objects.all().count(), 'ended': Execution.objects.filter(~Q(execution_end=None)).count()}



        # CurveMatching
        print('# CM Exec:', CurveMatchingResult.objects.all().count())
        print('# CM Exp:', CurveMatchingResult.objects.all().values(
            'execution_column__execution__experiment__id').distinct().count())

        return Response(result, status=HTTP_200_OK)
