from django.urls import path
from . import views

urlpatterns = [
    path('all_problems/', views.all_problems, name='all_problems'),
    path('user_problems/', views.user_problems, name='user_problems'),
]
