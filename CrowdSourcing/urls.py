from django.urls import path
import CrowdSourcing.Views as Views

urlpatterns = [
    path('API/getNextQuestion', Views.getNextQuestion.as_view(), name="getNextQuestion"),
    path('API/saveQuestionResult', Views.saveQuestionResult.as_view(), name="saveQuestionResult"),

]

