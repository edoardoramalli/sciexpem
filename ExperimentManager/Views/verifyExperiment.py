# Local import
import ExperimentManager.views as View
from ExperimentManager.Models import *
from ExperimentManager.exceptions import *
from ReSpecTh.OptimaPP import TranslatorOptimaPP, OptimaPP
from ReSpecTh.zenodo import *

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from django.db import transaction


class verifyExperiment(View.ExperimentManagerBaseView):
    viewName = 'verifyExperiment'
    paramsType = {'status': str, 'exp_id': int}
    required_groups = {'POST': ['VALIDATE']}

    def view_post(self, request):
        zenodo = False
        try:
            with transaction.atomic():
                exp = Experiment.objects.get(pk=self.exp_id)
                exp.status = self.status

                # Update the DOI
                if self.status == 'verified' and (exp.fileDOI is None or exp.fileDOI.startswith('tmp') or not exp.xml_file):
                    # TODO da unificare
                    bucket_url, publish_url, doi, deposition_id = reserved_doi()
                    zenodo = True
                    update_description(title=doi,
                                       description=exp.file_paper.references,
                                       deposition_id=deposition_id)

                    exp.fileDOI = doi

                    # Update the ReSpecTh
                    txt = TranslatorOptimaPP.create_OptimaPP_txt(experiment=exp,
                                                                 data_groups=exp.data_columns.all(),
                                                                 initial_species=exp.initial_species.all(),
                                                                 common_properties=exp.common_properties.all(),
                                                                 file_paper=exp.file_paper)
                    try:
                        xml, error = OptimaPP.txt_to_xml(txt)
                        if error:
                            raise OptimaPPError(error)
                        else:
                            exp.xml_file = xml
                            upload_respecth(file_string=xml, doi=doi, bucket_url=bucket_url)
                            publish_doi(publish_url)
                    except FileNotFoundError:
                        raise OptimaPPError('Impossible to generate ReSpecTh file using OptimaPP.')

                exp.save()

        except (ConstraintFieldExperimentError, OptimaPPError) as e:
            if zenodo:
                delete_doi(deposition_id)
            return Response(status=HTTP_400_BAD_REQUEST, data="verifyExperiment: " + str(e))

        except Exception as e:
            if zenodo:
                delete_doi(deposition_id)
            raise e

        return Response(status=HTTP_200_OK, data="Experiment verified successfully.")