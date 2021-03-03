from django.urls import path
import ExperimentManager.Views as Views

urlpatterns = [
    path('API/filterDataBase', Views.filterDataBase.as_view(), name="filterDataBase"),
    path('API/loadExperiment', Views.loadExperiment.as_view(), name="loadExperiment"),
    path('API/deleteElement', Views.deleteElement.as_view(), name="deleteElement"),
    path('API/requestProperty', Views.requestProperty.as_view(), name="requestProperty"),
    path('API/updateElement', Views.updateElement.as_view(), name="updateElement"),
    path('API/requestPropertyList', Views.requestPropertyList.as_view(), name="requestPropertyList"),
    path('API/verifyExperiment', Views.verifyExperiment.as_view(), name="verifyExperiment"),
    path('API/getCurveMatching', Views.getCurveMatching.as_view(), name="getExecution"),
    path('API/insertElement', Views.insertElement.as_view(), name="insertElement"),
]

