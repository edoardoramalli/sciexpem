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
    # DELETE
    path('API/deleteExperiment/<int:pk>', views.deleteExperiment, name="deleteExperiment"),
    # VALIDATE
    path('API/validateExperiment/', views.validateExperiment, name="insertExecution"),
]

