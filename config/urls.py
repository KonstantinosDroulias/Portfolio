from django.conf import settings
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.static import serve

from kd import views
from kd.feeds import LatestPosts
from kd.sitemaps import SITEMAPS

urlpatterns = [
    path("", views.home, name="home"),
    path("writing/", views.writing, name="writing"),
    path("writing/page/<int:page>/", views.writing, name="writing_page"),
    path("writing/topic/<slug:category>/", views.writing, name="category"),
    path("writing/tag/<slug:tag>/", views.writing, name="tag"),
    path("writing/<slug:slug>/", views.post_detail, name="post"),
    path("work/", views.work, name="work"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("cv/", views.cv, name="cv"),
    path("feed/", LatestPosts(), name="feed"),
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
    path("robots.txt", views.robots, name="robots"),
    path("admin/", include("kd.cms_urls")),
]
if settings.DEBUG:
    urlpatterns += [path("media/<path:path>", serve, {"document_root": settings.MEDIA_ROOT})]

handler404 = "kd.views.not_found"
handler500 = "kd.views.server_error"
