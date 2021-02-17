from django.urls import path
from ExperimentManager import views

urlpatterns = [
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

