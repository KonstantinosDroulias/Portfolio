"""First run: owner account, profile with photo, site settings and the launch posts.

    manage.py setup_site --username konstantinos      # prints a new password once
Safe to run again: it only creates what is missing.
"""
import secrets
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.management.base import BaseCommand

from kd.models import Category, Post, Profile, SiteSettings, Tag, make_avatar

SEED = Path(__file__).resolve().parents[2] / "seed"
ATH = ZoneInfo("Europe/Athens")

POSTS = [
    {
        "slug": "replacing-plugins-without-breaking-the-store",
        "title": "Replacing WooCommerce plugins without breaking a live store",
        "excerpt": "How I moved customgifts.gr off a page builder and a stack of plugins, and checked every URL, price and order before switching anything off.",
        "category": "E-commerce", "tags": ["WooCommerce", "WordPress", "SEO"],
        "date": datetime(2026, 11, 10, 10, 0, tzinfo=ATH),
    },
    {
        "slug": "one-system-behind-every-store",
        "title": "One system behind every store",
        "excerpt": "Why I stopped building one-off store sites and put a Django ERP in the middle, with every shop as a thin client that syncs with it.",
        "category": "Business systems", "tags": ["Django", "ERP", "WooCommerce"],
        "date": datetime(2026, 11, 17, 10, 0, tzinfo=ATH),
    },
]


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--username", default="konstantinos")
        parser.add_argument("--email", default="me@konstantinosdroulias.com")

    def handle(self, *args, **opts):
        User = get_user_model()
        user = User.objects.filter(username=opts["username"]).first()
        if not user:
            password = secrets.token_urlsafe(14)
            user = User.objects.create_superuser(opts["username"], opts["email"], password,
                                                 first_name="Konstantinos", last_name="Droulias")
            self.stdout.write(self.style.SUCCESS(f"Created {user.username} — password: {password}"))
        prof, _ = Profile.objects.get_or_create(user=user)
        if not prof.display_name:
            prof.display_name = "Konstantinos Droulias"
            prof.role_line = "Founder, DKN Media"
            prof.bio = ("Backend developer in Greece. I build business systems: ERPs, APIs, e-shops and automations, "
                        "and I write about what I learn building them.")
            prof.github = "https://github.com/KonstantinosDroulias"
        if not prof.photo:
            src = Path(settings.BASE_DIR) / "static" / "img" / "konstantinos.webp"
            with src.open("rb") as fh:
                prof.photo.save("konstantinos.webp", File(fh), save=False)
            with src.open("rb") as fh:
                prof.avatar.save(f"{user.pk}-konstantinos.webp", make_avatar(fh), save=False)
        prof.save()
        SiteSettings.load()

        for spec in POSTS:
            if Post.objects.filter(slug=spec["slug"]).exists():
                continue
            cat, _ = Category.objects.get_or_create(name=spec["category"], defaults={"slug": spec["category"].lower().replace(" ", "-")})
            post = Post.objects.create(
                slug=spec["slug"], title=spec["title"], excerpt=spec["excerpt"],
                body=(SEED / f"{spec['slug']}.md").read_text(), author=user, category=cat,
                status=Post.PUBLISHED, published_at=spec["date"])
            post.tags.set([Tag.objects.get_or_create(name=t, defaults={"slug": t.lower()})[0] for t in spec["tags"]])
            self.stdout.write(f"Post: {post.title}")
        self.stdout.write(self.style.SUCCESS("Site ready."))
