from django.db.models import Q
from django.shortcuts import render

from projects.models import Project, Tag


# Create your views here.

def index(request):
    projects = Project.objects.order_by('-created')[:3]
    context = {
        "projects": projects
    }
    return render(request, 'website/index.html', context)

def contact_me(request):
    context = {}
    return render(request, 'website/contact-me.html', context)


def about_me(request):
    projects = Project.objects.all()
    tags = Tag.objects.all()
    total_projects = projects.count()
    for tag in tags:
        project_count = tag.project_set.count()

        if total_projects > 0:
            tag.percentage = int((project_count / total_projects) * 100)
        else:
            tag.percentage = 0

    context = {
        "projects": projects,
        "tags": tags
    }
    return render(request, 'website/about-me.html', context)

def search(request):
    query = request.GET.get("search", "").strip()

    project_results = []
    post_results = []

    if query:
        project_results = Project.objects.filter(
            Q(title__icontains=query)
            | Q(short_description__icontains=query)
            | Q(content__icontains=query)
        ).distinct()

    context = {
        "query": query,
        "project_results": project_results,
        "post_results": post_results,
    }
    return render(request, "website/search.html", context)