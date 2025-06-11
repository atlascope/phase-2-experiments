from django.db import models


class Image(models.Model):
    name = models.CharField(max_length=255)
    tile_url = models.CharField(max_length=500)


class Nucleus(models.Model):
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    x = models.FloatField()
    y = models.FloatField()
    width = models.FloatField()
    height = models.FloatField()
    orientation = models.FloatField()

    class Meta:
        verbose_name_plural = "nuclei"
