from django.urls import path
from CurveMatching import views

urlpatterns = [
    path('API/executeCurveMatching', views.executeCurveMatching, name="executeCurveMatching"),
    path('API/createUpdateExecutionCurveMatching', views.createUpdateExecutionCurveMatching, name="createUpdateExecutionCurveMatching"),
    path('API/curveMatchingIsRunning', views.curveMatchingIsRunning, name="curveMatchingIsRunning"),

]
