from django.urls import path

from . import views

urlpatterns = [
    path('images/<int:image_id>', views.image_view, name='image_view'),
    path('', views.index, name='index'),
]
