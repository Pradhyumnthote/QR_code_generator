# decryptor/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # The root path maps to the home view
    path('decrypt/', views.decrypt_page, name='decrypt_page'),
]