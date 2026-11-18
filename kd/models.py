import math
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.text import slugify

from .markdown_render import render_markdown, word_count


def make_avatar(fileobj, size=256):
    """Square face crop. Transparent cutouts: crop the top of the figure; photos: top-centre square."""
    from PIL import Image, ImageOps

    im = ImageOps.exif_transpose(Image.open(fileobj))
    im = im.convert("RGBA")
    w, h = im.size
    bbox = im.getchannel("A").getbbox() or (0, 0, w, h)
    x0, y0, x1, y1 = bbox
    if bbox != (0, 0, w, h):
        side = max(32, int((x1 - x0) * 0.62))
        top = max(0, y0 - int(side * 0.06))
    else:
        side = min(w, h)
        top = 0 if h > w else 0
    cx = (x0 + x1) // 2
    left = min(max(0, cx - side // 2), max(0, w - side))
    crop = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    crop.paste(im.crop((left, top, left + side, top + side)), (0, 0))
    out = BytesIO()
    crop.resize((size, size), Image.LANCZOS).save(out, "WEBP", quality=88, method=6)
    return ContentFile(out.getvalue())


class Profile(models.Model):
    """Public author details for each CMS user."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=120, blank=True)
    role_line = models.CharField("Role", max_length=120, blank=True, help_text="Shown under your name, e.g. Founder, DKN Media")
    bio = models.TextField(blank=True, help_text="One or two sentences for the author box under posts.")
    photo = models.ImageField(upload_to="people/", blank=True)
    avatar = models.ImageField(upload_to="people/avatars/", blank=True, editable=False)
    github = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    instagram = models.URLField(blank=True)

    def __str__(self):
        return self.name

    @property
    def name(self):
        return self.display_name or self.user.get_full_name() or self.user.get_username()

    def set_photo(self, upload):
        self.photo.save(upload.name, upload, save=False)
        self.photo.open("rb")
        self.avatar.save(f"{self.user.pk}-{slugify(self.name)}.webp", make_avatar(self.photo), save=False)
        self.photo.close()

    @property
    def avatar_url(self):
        from django.templatetags.static import static
        return self.avatar.url if self.avatar else static("img/avatar.webp")

    @property
    def photo_url(self):
        from django.templatetags.static import static
        return self.photo.url if self.photo else static("img/konstantinos.webp")

    def links(self):
        return [(label, url) for label, url in (("GitHub", self.github), ("LinkedIn", self.linkedin), ("Instagram", self.instagram)) if url]


class SiteSettings(models.Model):
    """Single row: contact details and site-wide text that the owner edits in the CMS."""
    email = models.EmailField(default="me@konstantinosdroulias.com")
    based_in = models.CharField(max_length=120, default="Nea Smyrni, Athens")
    currently = models.CharField(max_length=200, default="Building business systems at DKN Media")
    agency_name = models.CharField(max_length=80, default="DKN Media")
    agency_url = models.URLField(default="https://dknmedia.gr")
    github = models.URLField(default="https://github.com/KonstantinosDroulias")
    linkedin = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    x = models.URLField("X", blank=True)
    cv = models.FileField(upload_to="cv/", blank=True, help_text="PDF")
    cv_updated = models.DateTimeField(null=True, blank=True)
    now_items = models.TextField(
        "Now", blank=True,
        help_text="One per line: Label | Text",
        default=(
            "Building | The Mygrafistas ERP: one Django system behind every store\n"
            "Running | DKN Media, consulting first, then the system\n"
            "Studying | Final year, BSc (Hons) Computer Science\n"
            "Writing | Notes on business systems, e-commerce and working with AI agents"
        ),
    )
    now_updated = models.DateField(default=timezone.localdate)
    notify_email = models.EmailField(blank=True, help_text="Where contact messages are emailed (when mail is set up on the server).")
    analytics_id = models.CharField(
        "Google Analytics ID", max_length=20, blank=True,
        help_text="Optional, e.g. G-XXXXXXX. When set, visitors are asked to accept before anything loads.")

    class Meta:
        verbose_name = "Site settings"

    def __str__(self):
        return "Site settings"

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def socials(self):
        return [(label, url) for label, url in (
            ("GitHub", self.github), ("LinkedIn", self.linkedin), ("Instagram", self.instagram), ("X", self.x)) if url]

    def now_rows(self):
        rows = []
        for line in self.now_items.splitlines():
            if not line.strip():
                continue
            label, _, text = line.partition("|")
            rows.append((label.strip(), text.strip()) if text else ("", label.strip()))
        return rows


class Category(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = self.slug or slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("category", args=[self.slug])


class Tag(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = self.slug or slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("tag", args=[self.slug])


class PostQuerySet(models.QuerySet):
    def live(self):
        return self.filter(status=Post.PUBLISHED, published_at__lte=timezone.now())


class Post(models.Model):
    DRAFT, PUBLISHED = "draft", "published"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    excerpt = models.TextField(max_length=320, blank=True, help_text="Short summary under the title. Also the meta description.")
    body = models.TextField(blank=True, help_text="Markdown")
    cover = models.ImageField(upload_to="covers/%Y/", blank=True)
    cover_alt = models.CharField(max_length=200, blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="posts")
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name="posts")
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")
    status = models.CharField(max_length=10, choices=[(DRAFT, "Draft"), (PUBLISHED, "Published")], default=DRAFT)
    published_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    seo_title = models.CharField("SEO title", max_length=70, blank=True)
    seo_description = models.CharField("SEO description", max_length=170, blank=True)

    objects = PostQuerySet.as_manager()

    class Meta:
        ordering = ["-published_at"]
        indexes = [models.Index(fields=["status", "-published_at"])]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("post", args=[self.slug])

    @property
    def is_live(self):
        return self.status == self.PUBLISHED and self.published_at <= timezone.now()

    @cached_property
    def body_html(self):
        return render_markdown(self.body)

    @property
    def reading_minutes(self):
        return max(1, math.ceil(word_count(self.body) / 200))

    @property
    def meta_description(self):
        return self.seo_description or self.excerpt


class Upload(models.Model):
    """Images added to posts from the editor."""
    file = models.ImageField(upload_to="uploads/%Y/%m/")
    alt = models.CharField(max_length=200, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    topic = models.CharField(max_length=40)
    message = models.TextField(max_length=5000)
    ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} <{self.email}>"


class ProjectQuerySet(models.QuerySet):
    def live(self):
        return self.filter(published=True)


class Project(models.Model):
    """Side projects, experiments and coursework shown on /projects/. Managed from the CMS."""
    title = models.CharField(max_length=120)
    kind = models.CharField("Type", max_length=60, blank=True, help_text="Short label, like “Machine learning” or “Web app”")
    year = models.CharField(max_length=20, blank=True, help_text="Like 2026 or 2025 — 2026")
    summary = models.TextField(max_length=600, help_text="Two or three sentences: what it is, what you built it with")
    stack = models.CharField(max_length=200, blank=True, help_text="Comma separated, like Django, React, Docker")
    url = models.URLField("Link", blank=True)
    link_label = models.CharField(max_length=80, blank=True, help_text="Shown instead of the address, like GitHub or Live site")
    order = models.PositiveIntegerField(default=0, help_text="Lower numbers show first")
    published = models.BooleanField("Show on the site", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProjectQuerySet.as_manager()

    class Meta:
        ordering = ["order", "-created_at"]

    def __str__(self):
        return self.title

    @property
    def stack_list(self):
        return [s.strip() for s in self.stack.split(",") if s.strip()]

    @property
    def link_text(self):
        if self.link_label:
            return self.link_label
        return self.url.split("://", 1)[-1].rstrip("/") if self.url else ""
