import requests
import tempfile
import json

from django.core.management.base import BaseCommand

from TCGA.models import Image, Nucleus

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        images = [
            dict(
                name='TCGA-3C-AALI-01Z-00-DX1',
                tile_url='http://parakon.khq:8088/api/v1/item/66d0bba8808445a354b9fbd3/tiles/',
                nuclei_url='https://data.kitware.com/api/v1/item/6849f52047746876d541ed7d/download'
            )
        ]
        for image in images:
            name = image.get('name')
            print(f'Creating {name}...')
            Image.objects.filter(name=name).delete()
            im = Image.objects.create(
                name=name,
                tile_url=image.get('tile_url'),
            )
            nuclei = []
            with tempfile.NamedTemporaryFile() as temp_file:
                response = requests.get(image.get('nuclei_url'), stream=True)
                nuclei = response.json()
            Nucleus.objects.bulk_create([
                Nucleus(
                    image=im,
                    x=nucleus.get('x'),
                    y=nucleus.get('y'),
                    width=nucleus.get('width'),
                    height=nucleus.get('height'),
                    orientation=nucleus.get('orientation'),
                ) for nucleus in nuclei
            ])

            print(f'Created Image {name} with {Nucleus.objects.filter(image=im).count()} Nuclei.')
