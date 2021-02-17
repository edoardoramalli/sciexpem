from django.urls import path
from CurveMatching import views

urlpatterns = [
    path('API/executeCurveMatching', views.executeCurveMatching, name="executeCurveMatching"),
]
