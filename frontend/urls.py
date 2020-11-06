from FrontEnd import views
from django.urls import path

urlpatterns = [
    path('', views.index),
    path('newpaper', views.FilePaperCreate.as_view(), name='newpaper'),
    path('newexperiment', views.ExperimentCreate.as_view(), name='newexperiment'),
    path('api/experiments/', views.ExperimentListAPI.as_view(), name="experiment-list-api"),
    path('api/experiments/filter', views.ExperimentFilteredListAPI.as_view(), name="experiment-filtered-list-api"),
    path('api/experiments/search', views.SearchExperiments.as_view(), name="search-experiment"),
    path('api/experiments/searchfields', views.experiment_search_fields, name="experiment-search-fields"),
    path('api/models/', views.ChemModelListAPI.as_view(), name="model-list-api"),
    path('api/experiment/<int:pk>', views.ExperimentDetailAPI.as_view(), name="experiment-detail-api"),
    path('api/experiment/curves/<int:pk>', views.experiment_curve_API, name="experiment-curves-api"),
    path('api/opensmoke/curves', views.experiment_models_curve_API, name="experiment-models-curve-api"),
    path('api/curve_matching_results', views.curve_matching_results_API, name='curve-matching-results-api'),
    path('api/curve_matching_global_results', views.curve_matching_global_results_API, name='curve-matching-results-api'),
    path('api/curve_matching_global_results_dict', views.curve_matching_global_results_dict_API, name='curve-matching-results-dict-api'),
    path('api/experiment/download/input_file/<int:pk>', views.download_input_file, name="download-input-file"),
    path('api/experiment/download/excel/<int:pk>', views.download_experiment_excel, name="download-experiment-excel"),
    path('api/curve_matching_global_results/download', views.download_cm_global, name="download-cm-global"),
    path('api/opensmoke/download/output', views.download_output_zip, name="download-output-zip"),
    path('input/data_excel', views.DataExcelUploadView.as_view(), name="data-excel-upload"),
    path('input/input_file', views.InputUploadView.as_view(), name="input-dic-upload"),
    path('input/submit', views.DetailFormView.as_view(), name="detail-submit"),
    path('input/submit_file', views.InputFileFormView.as_view(), name="input-file-submit"),
    path('api/opensmoke/species_names', views.opensmoke_names, name="opensmoke-names")
]