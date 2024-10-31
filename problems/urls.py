from django.urls import path
from . import views

urlpatterns = [
    path('<str:question_id>/', views.problem_detail, name='problem_detail'),
    path('problems/<str:question_id>/run_code/', views.run_code, name='run_code')
]
