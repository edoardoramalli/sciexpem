from FrontEnd import views
import FrontEnd.Views as Views
from django.urls import path

urlpatterns = [
    # path('input/data_excel', views.DataExcelUploadView.as_view(), name="data-excel-upload"),
    # path('input/input_file', views.InputUploadView.as_view(), name="input-dic-upload"),
    # path('input/os_input_file', views.OSInputUploadView.as_view(), name="os-input-dic-upload"),

    path('api/opensmoke/species_names', views.opensmoke_names, name="opensmoke-names"),
    path('api/opensmoke/fuels_names', views.fuels_names, name="fuels-names"),
    path('api/get_experiment_type_list', views.get_experiment_type_list, name="get_experiment_type_list"),
    path('api/get_chemModel_version_list', views.get_chemModel_version_list, name='get_chemModel_version_list'),
    path('api/get_username', views.get_username, name="get_username"),

    # path('api/get_experiment_data_columns/<int:pk>', views.get_experiment_data_columns,
    #      name="get_experiment_data_columns"),

    # path('api/get_reactor_type_list', views.get_reactor_type_list, name="get_reactor_type_list"),

    # NEW NEW
    path('API/getRawData', Views.getRawData.as_view(), name="getRawData"),
    path('API/getProfile', Views.getProfile.as_view(), name="getProfile"),
    path('API/addExecutionFiles', Views.addExecutionFiles.as_view(), name="addExecutionFiles"),
    path('API/getExecutionFileList', Views.getExecutionFileList.as_view(), name="getExecutionFileList"),
    path('API/getExecutionColumn', Views.getExecutionColumn.as_view(), name="getExecutionColumn"),
    path('API/addExecution', Views.addExecution.as_view(), name="addExecution"),
    path('API/getFile', Views.downloadFile.as_view(), name="downloadFile"),
    path('API/getPlotExperiment', Views.getPlotExperiment.as_view(), name="getPlotExperiment"),
    path('API/getPlotExecution', Views.getPlotExecution.as_view(), name="getPlotExecution"),
    path('API/getAllPlotExecution', Views.getAllPlotExecution.as_view(), name="getAllPlotExecution"),
    path('API/getHeatMapExecution', Views.getHeatMapExecution.as_view(), name="getHeatMapExecution"),
    path('API/getValidation', Views.getValidation.as_view(), name="getValidation"),
    path('API/getFuelValidation', Views.getFuelValidation.as_view(), name="getFuelValidation"),
    path('API/getWorld', Views.getWorld.as_view(), name="getWorld"),
    path('API/getIntervalAnalysis', Views.getIntervalAnalysis.as_view(), name="getIntervalAnalysis"),
    path('API/getWorldDiff', Views.getWorldDiff.as_view(), name="getWorldDiff"),
    path('API/getCluster', Views.getCluster.as_view(), name="getCluster"),
    path('API/getTargetValidation', Views.getTargetValidation.as_view(), name="getTargetValidation"),
    path('API/getPlotsValidation', Views.getPlotsValidation.as_view(), name="getPlotsValidation"),
    path('API/getParityPlot', Views.getParityPlot.as_view(), name="getParityPlot"),
    path('API/getDataFrameExecution', Views.getDataFrameExecution.as_view(), name="getDataFrameExecution"),

    path('API/prova', views.prova.as_view(), name="prova"),

]
