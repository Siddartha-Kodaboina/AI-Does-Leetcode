from django.urls import path
from .views import audio_page

urlpatterns = [
    path('', audio_page, name='audio_page'),
]
