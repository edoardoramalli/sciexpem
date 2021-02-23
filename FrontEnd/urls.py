from FrontEnd import views
from FrontEnd import newViews
from django.urls import path

urlpatterns = [
    path('api/experiments/', views.ExperimentListAPI.as_view(), name="experiment-list-api"),
    path('api/experiments/filter', views.ExperimentFilteredListAPI.as_view(), name="experiment-filtered-list-api"),
    path('api/experiments/search', views.SearchExperiments.as_view(), name="search-experiment"),
    path('api/experiments/searchfields', views.experiment_search_fields, name="experiment-search-fields"),
    path('api/models/', views.ChemModelListAPI.as_view(), name="model-list-api"),
    path('api/experiment/<int:pk>', views.ExperimentDetailAPI.as_view(), name="experiment-detail-api"),
    path('api/experiment/curves/<int:pk>', views.experiment_curve_API, name="experiment-curves-api"),
    path('api/experiment/info/<int:pk>', views.experiment_info_API, name="experiment-info-api"),
    path('api/opensmoke/curves', views.experiment_models_curve_API, name="experiment-models-curve-api"),
    path('api/curve_matching_results', views.curve_matching_results_API, name='curve-matching-results-api'),
    path('api/curve_matching_global_results', views.curve_matching_global_results_API, name='curve-matching-results-api'),
    path('api/curve_matching_global_results_dict', views.curve_matching_global_results_dict_API, name='curve-matching-results-dict-api'),
    path('api/experiment/download/input_file/<int:pk>', views.download_input_file, name="download-input-file"),
    path('api/experiment/download/respecth_file/<int:pk>', views.download_respecth_file, name="download-respecth-file"),
    path('api/experiment/download/excel/<int:pk>', views.download_experiment_excel, name="download-experiment-excel"),
    path('api/curve_matching_global_results/download', views.download_cm_global, name="download-cm-global"),
    path('api/opensmoke/download/output', views.download_output_zip, name="download-output-zip"),
    path('input/data_excel', views.DataExcelUploadView.as_view(), name="data-excel-upload"),
    path('input/input_file', views.InputUploadView.as_view(), name="input-dic-upload"),
    path('input/os_input_file', views.OSInputUploadView.as_view(), name="os-input-dic-upload"),

    path('api/opensmoke/species_names', views.opensmoke_names, name="opensmoke-names"),
    path('api/opensmoke/fuels_names', views.fuels_names, name="fuels-names"),
    path('api/get_username', views.get_username, name="get_username"),
    path('api/get_experiment_file/<int:pk>', views.get_experiment_file, name="get_os_input"),
    path('api/get_experiment_data_columns/<int:pk>', views.get_experiment_data_columns, name="get_experiment_data_columns"),
    path('api/get_experiment_type_list', views.get_experiment_type_list, name="get_experiment_type_list"),
    path('api/get_reactor_type_list', views.get_reactor_type_list, name="get_reactor_type_list"),

    # NEW


    path('api/getExperimentList', views.getExperimentList, name="getExperimentList"),
    path('api/getPropertyList', views.getPropertyList, name="getPropertyList"),
    path('api/getFilePaper', views.getFilePaper, name="getFilePaper"),


]