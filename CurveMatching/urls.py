from django.urls import path
from CurveMatching import views

urlpatterns = [
    path('API/executeCurveMatchingBase', views.executeCurveMatchingBase, name="executeCurveMatchingBase"),
    # path('API/prova', views.prova, name="prova"),
]
