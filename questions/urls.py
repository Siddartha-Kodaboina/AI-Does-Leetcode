from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_question, name='create_question'),
]
