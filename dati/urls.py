from django.urls import path
from . import views
from dati.views import index, email_readers

urlpatterns = [
    path('', index, name='index'),
    path('readers', email_readers, name='email_readers'),
]