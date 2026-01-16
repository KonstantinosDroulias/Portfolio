from django.urls import path
from . import views

urlpatterns = [
    path('projects', views.projects, name='projects'),
    path('project/<int:id>/', views.project, name='project'),
    path('projects/tag/<int:id>/', views.tag, name='tag'),
]