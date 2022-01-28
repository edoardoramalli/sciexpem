from django.urls import path
from OpenSmoke import views
from OpenSmoke.Views import *

urlpatterns = [
    path('API/startSimulation', views.startSimulation, name="startSimulation"),
    path('API/returnResult', views.returnResult, name='returnResult'),
    path('API/createFolderSimulation', views.createFolderSimulation, name='createFolderSimulation'),
    path('API/initializeSimulation', views.initializeSimulation, name='initializeSimulation'),



    path('API/getExecutions', getExecutions.as_view(), name='getExecutions'),
    path('API/startExecution', startExecution.as_view(), name='startExecution'),
    path('API/collectFiles', collectFiles.as_view(), name='collectFiles'),
    path('API/checkUpdate', checkUpdate.as_view(), name='checkUpdate'),
    path('API/getUpdate', getUpdate.as_view(), name='getUpdate'),

    # TODO in futuro portare tutte su una sola API
    path('API/Report/getReportWaitingExecution', getReportWaitingExecution.as_view(), name='getReportWaitingExecution'),
    path('API/Report/getReportRunningExecution', getReportRunningExecution.as_view(), name='getReportRunningExecution'),
    path('API/Report/getReportEndedWithErrorExecution', getReportEndedWithErrorExecution.as_view(), name='getReportEndedWithErrorExecution'),
    path('API/Report/getReportEndedWithNoErrorNoColumnsExecution', getReportEndedWithNoErrorNoColumnsExecution.as_view(), name='getReportEndedWithNoErrorNoColumnsExecution'),
    path('API/Report/getReportNoCurveMatchingExecution', getReportNoCurveMatchingExecution.as_view(), name='getReportNoCurveMatchingExecution'),
    path('API/Report/getReportNegativeCurveMatchingExecution', getReportNegativeCurveMatchingExecution.as_view(), name='getReportNegativeCurveMatchingExecution'),

    # path('API/getUpdate', getUpdate.as_view(), name='getUpdate'),
    # path('API/getUpdate', getUpdate.as_view(), name='getUpdate'),
]
