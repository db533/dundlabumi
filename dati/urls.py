from django.urls import path
from . import views
from dati.views import index

urlpatterns = [
    path('/',index, name='index'),
]