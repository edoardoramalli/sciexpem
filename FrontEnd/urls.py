from FrontEnd import views
import FrontEnd.Views as Views
from django.urls import path

urlpatterns = [
    path('input/data_excel', views.DataExcelUploadView.as_view(), name="data-excel-upload"),
    # path('input/input_file', views.InputUploadView.as_view(), name="input-dic-upload"),
    # path('input/os_input_file', views.OSInputUploadView.as_view(), name="os-input-dic-upload"),

    path('api/opensmoke/species_names', views.opensmoke_names, name="opensmoke-names"),
    path('api/opensmoke/fuels_names', views.fuels_names, name="fuels-names"),
    path('api/get_experiment_type_list', views.get_experiment_type_list, name="get_experiment_type_list"),
    path('api/get_username', views.get_username, name="get_username"),

    path('api/get_experiment_data_columns/<int:pk>', views.get_experiment_data_columns, name="get_experiment_data_columns"),


    # path('api/get_reactor_type_list', views.get_reactor_type_list, name="get_reactor_type_list"),


    # NEW NEW
    path('API/addExecutionFiles', Views.addExecutionFiles.as_view(), name="addExecutionFiles"),
    path('API/getExecutionFileList', Views.getExecutionFileList.as_view(), name="getExecutionFileList"),
    path('API/getExecutionColumn', Views.getExecutionColumn.as_view(), name="getExecutionColumn"),
    path('API/addExecution', Views.addExecution.as_view(), name="addExecution"),
    path('API/getFile', Views.downloadFile.as_view(), name="downloadFile"),
    path('API/getExperimentList', Views.getExperimentList.as_view(), name="getExperimentList"),
    path('API/getPropertyList', Views.getPropertyList.as_view(), name="getPropertyList"),
    path('API/getFilePaper', Views.getFilePaper.as_view(), name="getFilePaper"),
    path('API/getPlotExperiment', Views.getPlotExperiment.as_view(), name="getPlotExperiment"),
    path('API/getExecutionList', Views.getExecutionList.as_view(), name="getExecutionList"),
    path('API/getPlotExecution', Views.getPlotExecution.as_view(), name="getPlotExecution"),
    path('API/getAllPlotExecution', Views.getAllPlotExecution.as_view(), name="getAllPlotExecution"),
    path('API/getModelList', Views.getModelList.as_view(), name="getModelList"),
    path('API/getHeatMapExecution', Views.getHeatMapExecution.as_view(), name="getHeatMapExecution"),


    path('API/prova', views.prova.as_view(), name="prova"),




]