from django.urls import path
from ReSpecTh import views

urlpatterns = [
    path('API/executeOptimaPP', views.executeOptimaPP, name="executeOptimaPP"),
    path('API/loadXMLExperiment', views.loadXMLExperiment, name="loadXMLExperiment"),
]
