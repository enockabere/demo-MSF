from django.db import models

# Create your models here.


class Photo(models.Model):
    image = models.FileField(null=False, blank=False)
