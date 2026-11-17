from django.conf import settings

from .models import SiteSettings


DEFAULT_DESCRIPTION = ("Konstantinos Droulias builds websites, e-shops and the business systems behind them: "
                       "ERPs, APIs and automations. Writing about development, e-commerce and building software.")


def site(request):
    host = request.get_host().split(":")[0]
    return {
        "site": SiteSettings.load(),
        "SITE_URL": settings.SITE_URL,
        "canonical": settings.SITE_URL + request.path,
        "noindex_host": host in settings.NOINDEX_HOSTS,
        "meta_title": "Konstantinos Droulias — Backend developer in Greece",
        "meta_description": DEFAULT_DESCRIPTION,
        "show_adminbar": request.user.is_authenticated and request.user.is_staff,
    }
