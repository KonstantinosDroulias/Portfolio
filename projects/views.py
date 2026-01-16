from django.shortcuts import render
from projects.models import Project, Tag
from django.shortcuts import get_object_or_404

# Create your views here.

def projects(request):
    projects = Project.objects.all()
    tags = Tag.objects.all()

    context = {
        'projects': projects,
        'tags': tags,
    }
    return render(request, 'projects/projects.html', context)

def project(request, id):
    project = get_object_or_404(Project, id=id)
    tags = project.tags.all()

    context = {
        "project": project,
        "tags": tags,
    }
    return render(request, 'projects/project.html', context)

def tag(request, id):
    tag = get_object_or_404(Tag, id=id)
    projects = tag.project_set.all()
    tags = Tag.objects.all()

    context = {
        "tag": tag,
        "projects": projects,
        "tags": tags,
    }
    return render(request, 'projects/tag.html', context)