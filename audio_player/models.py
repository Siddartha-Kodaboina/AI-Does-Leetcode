
from django.db import models

class AudioBook(models.Model):
    title = models.CharField(max_length=255)
    audio_url = models.URLField(max_length=500)

    def __str__(self):
        return self.title
