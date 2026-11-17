import json
import logging
from itertools import groupby

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import EmailMessage
from django.core.paginator import EmptyPage, Paginator
from django.db.models import Count, Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.http import require_GET

from . import content
from .forms import ContactForm
from .models import Category, ContactMessage, Post, SiteSettings, Tag

log = logging.getLogger(__name__)
PER_PAGE = 12


def owner():
    """The first superuser is the site owner (photo, name and links on Home/About)."""
    User = get_user_model()
    return User.objects.filter(is_superuser=True).select_related("profile").order_by("pk").first()


def person_jsonld(site):
    user = owner()
    data = {
        "@context": "https://schema.org", "@type": "Person",
        "name": user.profile.name if user else "Konstantinos Droulias",
        "url": settings.SITE_URL + "/",
        "image": settings.SITE_URL + static("img/konstantinos.webp"),
        "jobTitle": "Backend Developer",
        "worksFor": {"@type": "Organization", "name": site.agency_name, "url": site.agency_url},
        "address": {"@type": "PostalAddress", "addressLocality": site.based_in.split(",")[0], "addressCountry": "GR"},
        "alumniOf": "University of Greater Manchester (New York College Athens)",
        "knowsAbout": ["Django", "Python", "Go", "PostgreSQL", "WooCommerce", "ERP systems", "E-commerce"],
        "sameAs": [url for _, url in site.socials()],
        "email": f"mailto:{site.email}",
    }
    return json.dumps(data, ensure_ascii=False)


def home(request):
    site = SiteSettings.load()
    website = {"@context": "https://schema.org", "@type": "WebSite", "name": "Konstantinos Droulias",
               "url": settings.SITE_URL + "/"}
    return render(request, "kd/home.html", {
        "nav": "home",
        "posts": Post.objects.live().select_related("category")[:4],
        "projects": [p for p in content.WORK if p.get("home")],
        "jsonld": [person_jsonld(site), json.dumps(website)],
        "person": owner(),
        "meta_title": "Konstantinos Droulias — Backend developer building business systems",
    })


def writing(request, page=1, category=None, tag=None):
    qs = Post.objects.live().select_related("category")
    active_cat = active_tag = None
    if category:
        active_cat = get_object_or_404(Category, slug=category)
        qs = qs.filter(category=active_cat)
    if tag:
        active_tag = get_object_or_404(Tag, slug=tag)
        qs = qs.filter(tags=active_tag)
    q = request.GET.get("q", "").strip()[:100]
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(excerpt__icontains=q) | Q(body__icontains=q))
    if "page" in request.GET:
        try:
            page = int(request.GET["page"])
        except ValueError:
            raise Http404
    paginator = Paginator(qs, PER_PAGE)
    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        raise Http404
    groups = [(year, list(items)) for year, items in groupby(page_obj.object_list, key=lambda p: p.published_at.year)]
    categories = Category.objects.filter(posts__status=Post.PUBLISHED).annotate(n=Count("posts")).distinct()

    if active_cat:
        base = active_cat.get_absolute_url()
        title, intro = active_cat.name, active_cat.description
    elif active_tag:
        base = active_tag.get_absolute_url()
        title, intro = f"#{active_tag.name}", ""
    else:
        base = reverse("writing")
        title, intro = "Writing", ""

    def page_url(n):
        if active_cat or active_tag:
            return f"{base}?page={n}" if n > 1 else base
        return reverse("writing_page", args=[n]) if n > 1 else base

    return render(request, "kd/writing.html", {
        "nav": "writing", "groups": groups, "page_obj": page_obj, "q": q,
        "categories": categories, "active_cat": active_cat, "active_tag": active_tag,
        "heading": title, "intro": intro,
        "total": Post.objects.live().count(),
        "older_url": page_url(page_obj.next_page_number()) if page_obj.has_next() else "",
        "newer_url": page_url(page_obj.previous_page_number()) if page_obj.has_previous() else "",
        "canonical_override": settings.SITE_URL + page_url(page_obj.number),
        "noindex": bool(q),
        "meta_title": (f"Search: {q} — Writing" if q else (f"{title} — Writing" if (active_cat or active_tag) else "Writing — Konstantinos Droulias"))
                      + (f" (page {page_obj.number})" if page_obj.number > 1 else ""),
        "meta_description": intro or "Articles and notes on business systems, Django, e-commerce, WooCommerce and building software, by Konstantinos Droulias.",
    })


def post_detail(request, slug):
    post = get_object_or_404(Post.objects.select_related("category", "author__profile").prefetch_related("tags"), slug=slug)
    can_edit = request.user.is_authenticated and request.user.is_staff and (
        request.user.is_superuser or post.author_id == request.user.pk)
    if not post.is_live and not can_edit:
        raise Http404
    live = Post.objects.live()
    prev_post = live.filter(published_at__lt=post.published_at).first()
    next_post = live.filter(published_at__gt=post.published_at).order_by("published_at").first()
    author = post.author.profile
    url = settings.SITE_URL + post.get_absolute_url()
    image = settings.SITE_URL + (post.cover.url if post.cover else static("img/og-default.jpg"))
    article = {
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": post.title, "description": post.meta_description,
        "image": [image], "url": url, "mainEntityOfPage": url,
        "datePublished": post.published_at.isoformat(), "dateModified": post.updated_at.isoformat(),
        "author": {"@type": "Person", "name": author.name, "url": settings.SITE_URL + "/about/"},
        "publisher": {"@type": "Person", "name": "Konstantinos Droulias", "url": settings.SITE_URL + "/"},
        "wordCount": len(post.body.split()),
        "keywords": [t.name for t in post.tags.all()],
    }
    if post.category:
        article["articleSection"] = post.category.name
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": settings.SITE_URL + "/"},
        {"@type": "ListItem", "position": 2, "name": "Writing", "item": settings.SITE_URL + "/writing/"},
        {"@type": "ListItem", "position": 3, "name": post.title, "item": url},
    ]}
    return render(request, "kd/post.html", {
        "nav": "writing", "post": post, "author": author, "can_edit": can_edit,
        "prev_post": prev_post, "next_post": next_post, "og_image": image, "share_url": url,
        "jsonld": [json.dumps(article, ensure_ascii=False), json.dumps(crumbs, ensure_ascii=False)],
        "noindex": not post.is_live,
        "meta_title": post.seo_title or f"{post.title} — Konstantinos Droulias",
        "og_title": post.seo_title or post.title,
        "meta_description": post.meta_description or post.title,
        "og_image_alt": post.cover_alt or post.title,
    })


def work(request):
    feature = content.WORK[0]
    return render(request, "kd/work.html", {"nav": "work", "feature": feature, "projects": content.WORK[1:],
        "meta_title": "Work — Konstantinos Droulias",
        "meta_description": "Business systems, e-shops and tools by Konstantinos Droulias: the DKN Media agency, the Mygrafistas ERP, a DTF printing platform, online stores and side projects."})


def about(request):
    site = SiteSettings.load()
    return render(request, "kd/about.html", {
        "nav": "about", "what": content.WHAT_I_DO, "tools": content.TOOLS, "person": owner(),
        "jsonld": [person_jsonld(site)],
        "meta_title": "About — Konstantinos Droulias",
        "meta_description": "Konstantinos Droulias is a backend developer and final-year Computer Science student in Greece who builds ERPs, APIs, e-commerce platforms and automations.",
    })


def _client_ip(request):
    return request.META.get("HTTP_X_REAL_IP") or request.META.get("REMOTE_ADDR")


def contact(request):
    sent = request.GET.get("sent") == "1"
    form = ContactForm(request.POST or None)
    if request.method == "POST":
        ip = _client_ip(request)
        key = f"contact:{ip}"
        hits = cache.get(key, 0)
        if form.is_valid() and not form.cleaned_data.get("website"):
            if hits >= 5:
                form.add_error(None, "Too many messages from your network. Please email me instead.")
            else:
                cache.set(key, hits + 1, 3600)
                msg = ContactMessage.objects.create(
                    name=form.cleaned_data["name"], email=form.cleaned_data["email"],
                    topic=form.cleaned_data["topic"], message=form.cleaned_data["message"], ip=ip)
                site = SiteSettings.load()
                try:
                    EmailMessage(
                        subject=f"[konstantinosdroulias.com] {msg.topic}: {msg.name}",
                        body=f"{msg.message}\n\n— {msg.name} <{msg.email}>",
                        to=[site.notify_email or site.email], reply_to=[msg.email],
                    ).send(fail_silently=False)
                except Exception:  # message is saved in the CMS either way
                    log.exception("contact mail failed")
                return redirect(reverse("contact") + "?sent=1#form")
        elif form.is_valid():  # honeypot filled: pretend it worked
            return redirect(reverse("contact") + "?sent=1#form")
    return render(request, "kd/contact.html", {"nav": "contact", "form": form, "sent": sent and request.method == "GET",
        "meta_title": "Contact — Konstantinos Droulias",
        "meta_description": "Get in touch with Konstantinos Droulias about a website, an e-shop or a business system."})


def cv(request):
    site = SiteSettings.load()
    if site.cv:
        return redirect(site.cv.url)
    return redirect(static("cv/konstantinos-droulias-cv.pdf"))


@require_GET
def robots(request):
    host = request.get_host().split(":")[0]
    if host in settings.NOINDEX_HOSTS:
        body = "User-agent: *\nDisallow: /\n"
    else:
        body = f"User-agent: *\nDisallow: /admin/\nAllow: /\n\nSitemap: {settings.SITE_URL}/sitemap.xml\n"
    return HttpResponse(body, content_type="text/plain")


def not_found(request, exception=None):
    return render(request, "kd/404.html", {"noindex": True, "meta_title": "Page not found — Konstantinos Droulias"}, status=404)


def server_error(request):
    return render(request, "kd/500.html", status=500)
