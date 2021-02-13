from django.urls import path
from ReSpecTh import views

urlpatterns = [
    path('API/executeOptimaPP', views.executeOptimaPP, name="executeOptimaPP"),
    # NEW
    path('API/convertList', views.convertList, name="covertList"),
    path('API/getReactors', views.getReactors, name="getReactors"),
]
