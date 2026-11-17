from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Category, Post


class Https(Sitemap):
    protocol = "https"

    def get_urls(self, page=1, site=None, protocol=None):
        from django.conf import settings
        from types import SimpleNamespace
        domain = settings.SITE_URL.split("://", 1)[1]
        return super().get_urls(page=page, site=SimpleNamespace(domain=domain, name=domain), protocol="https")


class StaticSitemap(Https):
    changefreq = "monthly"

    def items(self):
        return ["home", "writing", "work", "about", "contact", "privacy"]

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return 1.0 if item == "home" else 0.2 if item == "privacy" else 0.7


class PostSitemap(Https):
    changefreq = "monthly"
    priority = 0.8

    def items(self):
        return Post.objects.live()

    def lastmod(self, obj):
        return obj.updated_at


class CategorySitemap(Https):
    changefreq = "weekly"
    priority = 0.4

    def items(self):
        return Category.objects.filter(posts__status=Post.PUBLISHED).distinct()


SITEMAPS = {"pages": StaticSitemap, "posts": PostSitemap, "topics": CategorySitemap}
