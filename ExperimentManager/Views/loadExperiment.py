# Local import
import ExperimentManager.views as View
from ExperimentManager.Views.insertElement import checkExperiment
from ExperimentManager.Models import *
from ExperimentManager.exceptions import *
from ReSpecTh.ReSpecThParser import ReSpecThParser

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from django.db import transaction


def getSpecie(diz):
    preferredKey = diz.pop('preferredKey')
    CAS = diz.pop('CAS')
    InChI = diz.pop('InChI')
    SMILES = diz.pop('SMILES')
    chemName = diz.pop('chemName')

    if not InChI:
        raise ValueError('The InChI of the specie is mandatory!')

    specie = Specie.objects.get(InChI=InChI)

    if specie is None:
        raise ValueError(
            'The specie is not in the database. Contact admin!')  # per creare una specie manca la formula CxHyOz
    else:
        # if not all([preferredKey == specie.preferredKey, InChI == specie.InChI, SMILES == specie.SMILES,
        #  chemName == specie.chemName, CAS == specie.CAS]):
        #     pass
        #     # TODO warning? bloccare inserimento?
        #     # raise ValueError('The InChI {} of the specie exists but the other fields are different!'.format(InChI))
        # else:
        #     diz['specie'] = specie
        #     return diz

        return specie


def respecth_text_to_experiment(username, file):
    status = "unverified"
    with transaction.atomic():
        respecth_obj = ReSpecThParser.from_string(file)

        # Check Mandatory Field
        reactor = respecth_obj.apparatus
        experiment_type = respecth_obj.experiment_type
        fileDOI = respecth_obj.fileDOI
        comment = respecth_obj.comment
        reactor_modes = respecth_obj.modes

        # TODO questi controlli dovrebbero essere inutili dal momento che checkExp dovrebbe farli!
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

            # TODO non viene controllato se esiste già la reference ma il doi si

            reference_doi = respecth_obj.getBiblioDOI()
            if reference_doi is not None and FilePaper.objects.filter(reference_doi=reference_doi).exists():
                paper = FilePaper.objects.get(reference_doi=reference_doi)
            else:
                paper = FilePaper(description=respecth_obj.getBiblio(),
                                  reference_doi=respecth_obj.getBiblioDOI(),
                                  author=respecth_obj.getBiblioAuthor(),
                                  title=respecth_obj.getBiblioTitle(),
                                  journal=respecth_obj.getBiblioJournal(),
                                  page=respecth_obj.getBiblioPage(),
                                  year=respecth_obj.getBiblioYear(),
                                  volume=respecth_obj.getBiblioVolume(),
                                  )
                paper.save()

            e = Experiment(reactor=reactor,
                           reactor_modes=reactor_modes,
                           experiment_type=experiment_type,
                           fileDOI=fileDOI,
                           ignition_type=ignition_type,
                           file_paper=paper,
                           xml_file=file,
                           status=status,
                           comment=comment,
                           username=username)
            e.save()

            data_groups = respecth_obj.extract_columns_multi_dg()

            for group in data_groups:
                association = {}
                tmp = []
                # Le incertezze sono tutte in cima alla lista. Ho la certezza di aver creato le precedenti
                for column in group:
                    if 'uncertainty_reference' not in column:
                        tmp.append(column)
                    else:
                        tmp.insert(0, column)

                for column in tmp:
                    current_id = column.pop('id')
                    if 'uncertainty_reference' in column:
                        uncertainty_reference = column['uncertainty_reference']
                        column['uncertainty_reference'] = None
                        current_column = DataColumn(experiment=e, **column)
                        current_column.save()
                        association[uncertainty_reference] = current_column
                    else:
                        if current_id in association:
                            column['uncertainty_reference'] = association[current_id]
                        species_object_list = []
                        species = column.pop('species')
                        for specie in species:
                            if 'chemName' in specie:
                                specie.pop('chemName')

                            query_specie = Specie.objects.filter(**specie)

                            if len(query_specie) == 1:
                                current_specie = query_specie[0]
                            elif len(query_specie) == 0:
                                raise ValueError('The desired specie not exist in the database. Contact admin. {}'.format(specie))
                            else:
                                raise ValueError('Ambiguity to select specie in database. Contact admin.')
                            species_object_list.append(current_specie)


                        current_column = DataColumn(experiment=e, **column)
                        current_column.save()

                        for specie_object in species_object_list:
                            current_column.species_object.add(specie_object)

            common_properties = list(respecth_obj.common_properties().values())

            for c in common_properties:
                cp = CommonProperty(experiment=e, **c)
                cp.save()

            initial_species = respecth_obj.initial_composition()

            for i in initial_species:
                ip = InitialSpecie(experiment=e, **{'specie': getSpecie(i), **i})
                ip.save()

            checkExperiment(e, opensmoke=False)


class loadExperiment(View.ExperimentManagerBaseView):
    viewName = 'loadExperiment'
    paramsType = {'format_file': str, 'file_text': str}
    required_groups = {'POST': ['WRITE']}

    def view_post(self, request):
        username = request.user.username

        if self.format_file == 'XML_ReSpecTh':
            try:
                respecth_text_to_experiment(username, self.file_text)
            except ExperimentConsistencyError as e:
                return Response(self.viewName + ": " + str(e), status=HTTP_400_BAD_REQUEST)
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
