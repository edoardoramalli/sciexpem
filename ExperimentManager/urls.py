from django.urls import path
from ExperimentManager import views

urlpatterns = [
    # FILTER
    path('API/filterExperiment', views.filterExperiment, name="filterExperiment"),
    path('API/filterChemModel', views.filterChemModel, name="filterModel"),
    path('API/filterExecution', views.filterExecution, name="filterExecution"),
    path('API/filterCurveMatchingResult', views.filterCurveMatchingResult, name="filterCurveMatchingResult"),
    # INSERT
    path('API/insertExperiment', views.insertExperiment, name="insertExperiment"),
    path('API/insertChemModel', views.insertChemModel, name="insertChemModel"),
    path('API/insertExecution', views.insertExecution, name="insertExecution"),
    path('API/loadXMLExperiment', views.loadXMLExperiment, name="loadXMLExperiment"),
    path('API/loadXMLExperimentSimple', views.loadXMLExperimentSimple, name="loadXMLExperimentSimple"),
    # UPDATE
    path('API/insertOSFile/<int:pk>', views.insertOSFile, name="insertOSFile"),
    path('API/insertOSFileAPI/', views.insertOSFileAPI, name="insertOSFileAPI"),
    # DELETE
    # path('API/deleteExperiment/<int:pk>', views.deleteExperiment, name="deleteExperiment"),
    # VERIFY
    path('API/validateExperiment/', views.validateExperiment, name="insertExperiment"),
    # ANALYSIS
    path('API/analyzeExecution/', views.analyzeExecution, name="analyzeExecution"),


    # ---- NEW ----
    path('API/filterDataBase', views.filterDataBase, name="filterDataBase"),
    path('API/requestProperty', views.requestProperty, name="requestProperty"),
    path('API/loadExperiment', views.loadExperiment, name="loadExperiment"),
    path('API/updateElement', views.updateElement, name="updateElement"),
    path('API/verifyExperiment', views.verifyExperiment, name="verifyExperiment"),
    path('API/insertElement', views.insertElement, name="insertElement"),
    path('API/deleteElement', views.deleteElement, name="deleteElement"),

]

