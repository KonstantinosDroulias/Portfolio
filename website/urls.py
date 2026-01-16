from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path("search", views.search, name="search"),
    path('contact-me', views.contact_me, name='contact-me'),
    path('about-me', views.about_me, name='about-me'),
]