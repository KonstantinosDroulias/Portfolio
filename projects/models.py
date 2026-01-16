from django.contrib.auth.models import User
from django.db import models

# Create your models here.

class Tag(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Project(models.Model):
    featured_image = models.ImageField(upload_to='projects/', blank=True, null=True)
    title = models.CharField(max_length=100)
    short_description = models.TextField(null=True, blank=True)
    content = models.TextField()

    tags = models.ManyToManyField(Tag)

    github_link = models.URLField(null=True, blank=True)
    figma_link = models.URLField(null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Gallery(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='projects/gallery/', blank=True, null=True)
    caption = models.CharField(max_length=255, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.title} + {self.caption}"