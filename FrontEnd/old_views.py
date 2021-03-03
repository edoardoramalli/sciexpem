# TODO: rivedere, groupby df
@api_view(['GET'])
def download_cm_global(request):
    exp_ids = request.query_params.getlist('experiments[]', None)
    chem_models_ids = request.query_params.getlist('chemModels[]', None)

    cmr = models.CurveMatchingResult.objects.filter(execution_column__execution__chemModel__in=chem_models_ids,
                                                    execution_column__execution__experiment__in=exp_ids)

    result = []
    for i in cmr:
        if i.index is None or i.error is None:
            continue

        model_name = i.execution_column.execution.chemModel.name
        experiment_DOI = i.execution_column.execution.experiment.fileDOI
        execution_column = i.execution_column
        name = execution_column.name if not execution_column.species else execution_column.species[0]

        r = dict()
        r['model'] = model_name
        r['experiment'] = experiment_DOI
        r['name'] = name
        r['index'] = float(i.index)
        r['error'] = float(i.error)
        result.append(r)

    df = pd.DataFrame.from_dict(result)[['model', 'experiment', 'name', 'index', 'error']]
    df = df.groupby(["model", "name"]).mean()

    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer)
    writer.save()

    # FileResponse sets the Content-Disposition header so that browsers
    # present the option to save the file.
    response = HttpResponse(output.getvalue())
    response['content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response['Content-Disposition'] = 'attachment; filename= curve_matching.xlsx'

    return response

@api_view(['GET'])
def download_output_zip(request):
    output_root = Path(__location__) / 'output_experiments'
    exp_id = request.query_params.get('experiment', None)
    chem_models = request.query_params.getlist('chemModels[]', None)

    fp = OpenSmoke.retrieve_opensmoke_execution(exp_id, model_ids=chem_models, output_root=output_root)
    file = io.BytesIO()
    utils.zip_folders(file, fp, "{}__{}".format(exp_id, "-".join(chem_models)), remove_trailing=output_root)

    response = HttpResponse(file.getvalue())
    response['content-type'] = 'application/octet-stream'
    response['Content-Disposition'] = "attachment; filename={}__{}.zip".format(exp_id, "-".join(chem_models))

    return response
