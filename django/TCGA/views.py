import json
from django.shortcuts import render

from .models import Image, Nucleus


def index(request):
    images = Image.objects.all()
    return render(request, 'index.html', dict(images=images))


def image_view(request, image_id):
    image = Image.objects.get(id=image_id)
    nuclei = Nucleus.objects.filter(image=image)
    return render(request, 'image_view.html', dict(
        tile_url=image.tile_url,
        nuclei=json.dumps([
            dict(x=n.x, y=n.y, width=n.width, height=n.height, orientation=n.orientation)
            for n in nuclei
        ])
    ))
