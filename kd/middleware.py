from django.conf import settings


class RobotsHeaderMiddleware:
    """noindex on preview hosts, the CMS and search results."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        host = request.get_host().split(":")[0]
        if host in settings.NOINDEX_HOSTS or request.path.startswith("/admin/"):
            response["X-Robots-Tag"] = "noindex, nofollow"
        if request.path.startswith("/admin/") or request.user.is_authenticated:
            response["Cache-Control"] = "private, no-store"
        return response
