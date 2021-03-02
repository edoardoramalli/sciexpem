# Local import
import ExperimentManager.views as View
from ExperimentManager.Models import *
from ExperimentManager.exceptions import *
from ReSpecTh.ReSpecThParser import ReSpecThParser

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from django.db import transaction


def respecth_text_to_experiment(username, file):
    status = "unverified"
    with transaction.atomic():
        respecth_obj = ReSpecThParser.from_string(file)

        # Check Mandatory Field
        reactor = respecth_obj.apparatus
        experiment_type = respecth_obj.experiment_type
        fileDOI = respecth_obj.fileDOI

        if not reactor:
            raise MandatoryFieldExperimentError("Reactor")
        elif not experiment_type:
            raise MandatoryFieldExperimentError("Experiment type")
        elif not fileDOI:
            raise MandatoryFieldExperimentError("File DOI")

        # check duplicates
        if Experiment.objects.filter(fileDOI=fileDOI).exists():
            raise DuplicateExperimentError
        else:
            ignition_type = respecth_obj.get_ignition_type()

            # TODO non viene controllato se c'è il DOI
            # TODO non viene controllato se esiste già

            paper = FilePaper(references=respecth_obj.getBiblio())
            paper.save()

            e = Experiment(reactor=reactor,
                           experiment_type=experiment_type,
                           fileDOI=fileDOI,
                           ignition_type=ignition_type,
                           file_paper=paper,
                           xml_file=file,
                           status=status,
                           username=username)
            e.save()

            columns_groups = respecth_obj.extract_columns_multi_dg()

            for g in columns_groups:
                for c in g:
                    co = DataColumn(experiment=e, **c)
                    co.save()

            common_properties = respecth_obj.common_properties()

            for c in common_properties:
                cp = CommonProperty(experiment=e, **c)
                cp.save()

            initial_species = respecth_obj.initial_composition()

            for i in initial_species:
                ip = InitialSpecie(experiment=e, **i)
                ip.save()


class loadExperiment(View.ExperimentManagerBaseView):
    viewName = 'loadExperiment'
    paramsType = {'format_file': str, 'file_text': str}
    required_groups = {'POST': ['WRITE']}

    def view_post(self, request):
        username = request.user.username

        if self.format_file == 'XML_ReSpecTh':
            try:
                respecth_text_to_experiment(username, self.file_text)
            except DuplicateExperimentError:
                return Response(status=HTTP_400_BAD_REQUEST,
                                data=self.viewName + ": Duplicated Experiment.")
            except MandatoryFieldExperimentError as e:
                return Response(status=HTTP_400_BAD_REQUEST,
                                data=self.viewName + ": " + str(e))
            except ConstraintFieldExperimentError as e:
                return Response(status=HTTP_400_BAD_REQUEST,
                                data=self.viewName + ": " + str(e))

        else:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data=self.viewName + ": Format Not supported.")

        return Response("Experiment inserted successfully.", status=HTTP_200_OK)
