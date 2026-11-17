from django.conf import settings
from django.contrib.syndication.views import Feed

from .models import Post


class LatestPosts(Feed):
    title = "Konstantinos Droulias — Writing"
    link = "/writing/"
    description = "Notes on business systems, e-commerce and building software."

    def items(self):
        return Post.objects.live().select_related("category", "author__profile")[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.body_html

    def item_pubdate(self, item):
        return item.published_at

    def item_updateddate(self, item):
        return item.updated_at

    def item_author_name(self, item):
        return item.author.profile.name

    def item_categories(self, item):
        return [item.category.name] if item.category else []

    def item_link(self, item):
        return settings.SITE_URL + item.get_absolute_url()
