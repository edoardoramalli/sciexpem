from django.urls import path
from OpenSmoke import views

urlpatterns = [
    path('API/startSimulation', views.startSimulation, name="startSimulation"),
    path('API/returnResult', views.returnResult, name='returnResult')
]
