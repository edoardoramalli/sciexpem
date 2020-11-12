def create_lines(delimiter="\t", **kwargs):
    txt = ""
    keys = kwargs.keys()
    for key in keys:
        c_key = key.replace("_", " ")
        txt += c_key + ":" + delimiter + str(kwargs[key]) + "\n"

    return txt


def create_header(experiment, file_paper):
    txt = ""
    if file_paper.title:
        txt += create_lines(Reference_description=file_paper.title)
    if file_paper.reference_doi:
        txt += create_lines(Reference_DOI=file_paper.reference_doi)

    txt += create_lines(Specification_version=2.2,
                        File_DOI=experiment.fileDOI,  # M
                        Experiment_type=experiment.experiment_type,  # M
                        Apparatus=experiment.reactor)  # M
    return txt


def create_RCM(experiment, data_groups, initial_species, common_properties, file_paper):
    pass


a = create_lines(edo_ramalli=12, ele=323)
print(a)
