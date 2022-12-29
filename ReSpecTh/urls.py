from django.urls import path
from ReSpecTh import views

urlpatterns = [
    path('API/executeOptimaPP', views.executeOptimaPP, name="executeOptimaPP"),
    path('API/executeOptimaPPExperiment', views.executeOptimaPPExperiment, name="executeOptimaPP"),
    path('API/createTxtOptimaPP', views.createTxtOptimaPP, name='createTxtOptimaPP'),
    path('API/executeReSpecThConverter', views.executeReSpecThConverter, name='executeReSpecThConverter'),
    # NEW
    path('API/convertList', views.convertList, name="covertList"),
    # TODO questa può essere harcodata nell' UI
    path('API/getReactors', views.getReactors, name="getReactors"),
]
