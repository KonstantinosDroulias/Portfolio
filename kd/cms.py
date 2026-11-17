"""The private CMS at /admin/: sign-in, posts, messages, site settings, profile, users."""
from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.core.cache import cache
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import CVForm, NewUserForm, PostForm, ProfileForm, SiteSettingsForm
from .markdown_render import render_markdown
from .models import Category, ContactMessage, Post, Profile, SiteSettings, Upload


def staff_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_authenticated and request.user.is_active and request.user.is_staff):
            return redirect(f"/admin/login/?next={request.path}")
        Profile.objects.get_or_create(user=request.user)
        return view(request, *args, **kwargs)
    return wrapper


def owner_required(view):
    @wraps(view)
    @staff_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseForbidden("Only the site owner can open this page.")
        return view(request, *args, **kwargs)
    return wrapper


def _ctx(request, section, **extra):
    extra.update(section=section, unread=ContactMessage.objects.filter(read=False).count() if request.user.is_superuser else 0)
    return extra


# ---------- sign in ----------

def login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("cms:dashboard")
    ip = request.META.get("HTTP_X_REAL_IP") or request.META.get("REMOTE_ADDR")
    key = f"login-fail:{ip}"
    error = ""
    nxt = request.GET.get("next") or request.POST.get("next") or "/admin/"
    if not url_has_allowed_host_and_scheme(nxt, {request.get_host()}, require_https=request.is_secure()):
        nxt = "/admin/"
    if request.method == "POST":
        fails = cache.get(key, 0)
        if fails >= 8:
            error = "Too many attempts. Try again in 15 minutes."
        else:
            user = authenticate(request, username=request.POST.get("username", "").strip(), password=request.POST.get("password", ""))
            if user and user.is_staff:
                login(request, user)
                cache.delete(key)
                return redirect(nxt)
            cache.set(key, fails + 1, 900)
            error = "Wrong username or password."
    return render(request, "cms/login.html", {"error": error, "next": nxt, "username": request.POST.get("username", "")})


@require_POST
def logout_view(request):
    logout(request)
    return redirect("/")


# ---------- dashboard ----------

@staff_required
def dashboard(request):
    posts = Post.objects.select_related("category")
    if not request.user.is_superuser:
        posts = posts.filter(author=request.user)
    return render(request, "cms/dashboard.html", _ctx(
        request, "dashboard",
        recent=posts[:6],
        n_live=posts.filter(status=Post.PUBLISHED).count(),
        n_draft=posts.filter(status=Post.DRAFT).count(),
        inbox=ContactMessage.objects.all()[:4] if request.user.is_superuser else [],
    ))


# ---------- posts ----------

def _own_posts(user):
    qs = Post.objects.select_related("category", "author__profile")
    return qs if user.is_superuser else qs.filter(author=user)


@staff_required
def post_list(request):
    status = request.GET.get("status", "")
    qs = _own_posts(request.user)
    if status in (Post.DRAFT, Post.PUBLISHED):
        qs = qs.filter(status=status)
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(title__icontains=q)
    return render(request, "cms/posts.html", _ctx(request, "posts", posts=qs, status=status, q=q))


@staff_required
def post_edit(request, pk=None):
    post = get_object_or_404(_own_posts(request.user), pk=pk) if pk else Post(author=request.user)
    form = PostForm(request.POST or None, request.FILES or None, instance=post, user=request.user)
    if request.method == "POST" and form.is_valid():
        if "author" not in form.fields:
            form.instance.author = post.author if post.pk else request.user
        if form.cleaned_data["status"] == Post.PUBLISHED and "publish_now" in request.POST:
            form.instance.published_at = timezone.now()
        saved = form.save()
        messages.success(request, "Published." if saved.status == Post.PUBLISHED else "Draft saved.")
        return redirect("cms:post_edit", pk=saved.pk)
    return render(request, "cms/post_edit.html", _ctx(
        request, "posts", form=form, post=post, categories=Category.objects.all()))


@staff_required
@require_POST
def post_delete(request, pk):
    post = get_object_or_404(_own_posts(request.user), pk=pk)
    title = post.title
    post.delete()
    messages.success(request, f"Deleted “{title}”.")
    return redirect("cms:posts")


@staff_required
@require_POST
def preview(request):
    return JsonResponse({"html": render_markdown(request.POST.get("body", ""))})


@staff_required
@require_POST
def upload(request):
    f = request.FILES.get("file")
    if not f or not (f.content_type or "").startswith("image/"):
        return JsonResponse({"error": "Choose an image file."}, status=400)
    if f.size > 10 * 1024 * 1024:
        return JsonResponse({"error": "Images must be under 10 MB."}, status=400)
    from PIL import Image
    try:
        Image.open(f).verify()
        f.seek(0)
    except Exception:
        return JsonResponse({"error": "That file is not a readable image."}, status=400)
    up = Upload.objects.create(file=f, uploaded_by=request.user)
    return JsonResponse({"url": up.file.url})


# ---------- messages ----------

@owner_required
def inbox(request):
    return render(request, "cms/messages.html", _ctx(request, "messages", items=ContactMessage.objects.all()[:200]))


@owner_required
@require_POST
def message_action(request, pk):
    msg = get_object_or_404(ContactMessage, pk=pk)
    action = request.POST.get("action")
    if action == "delete":
        msg.delete()
    elif action == "read":
        msg.read = True
        msg.save(update_fields=["read"])
    elif action == "unread":
        msg.read = False
        msg.save(update_fields=["read"])
    return redirect("cms:messages")


# ---------- site settings + CV ----------

@owner_required
def site_settings(request):
    site = SiteSettings.load()
    form = SiteSettingsForm(request.POST or None, instance=site, prefix="s")
    cv_form = CVForm()
    if request.method == "POST":
        if "upload_cv" in request.POST:
            cv_form = CVForm(request.POST, request.FILES)
            if cv_form.is_valid():
                if site.cv:
                    site.cv.delete(save=False)
                site.cv.save("konstantinos-droulias-cv.pdf", cv_form.cleaned_data["cv"], save=False)
                site.cv_updated = timezone.now()
                site.save()
                messages.success(request, "CV uploaded. The Download CV button now serves it.")
                return redirect("cms:settings")
            form = SiteSettingsForm(instance=site, prefix="s")
        elif "remove_cv" in request.POST:
            if site.cv:
                site.cv.delete(save=False)
                site.cv_updated = None
                site.save()
            messages.success(request, "CV removed. The button falls back to the built-in CV.")
            return redirect("cms:settings")
        elif form.is_valid():
            form.save()
            messages.success(request, "Settings saved.")
            return redirect("cms:settings")
    return render(request, "cms/settings.html", _ctx(request, "settings", form=form, cv_form=cv_form, site=site))


# ---------- profile ----------

@staff_required
def profile(request):
    prof = request.user.profile
    form = ProfileForm(request.POST or None, request.FILES or None, instance=prof, prefix="p")
    pw_form = PasswordChangeForm(request.user, request.POST if "change_password" in request.POST else None)
    if request.method == "POST":
        if "change_password" in request.POST:
            form = ProfileForm(instance=prof, prefix="p")
            if pw_form.is_valid():
                user = pw_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password changed.")
                return redirect("cms:profile")
        elif form.is_valid():
            form.save()
            messages.success(request, "Profile saved.")
            return redirect("cms:profile")
    return render(request, "cms/profile.html", _ctx(request, "profile", form=form, pw_form=pw_form, prof=prof))


# ---------- users ----------

@owner_required
def users(request):
    User = get_user_model()
    form = NewUserForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        u = User.objects.create_user(d["username"], d["email"], d["password"], is_staff=True, is_superuser=d["is_superuser"])
        Profile.objects.update_or_create(user=u, defaults={"display_name": d["display_name"]})
        messages.success(request, f"Added {u.username}. They can sign in at /admin/.")
        return redirect("cms:users")
    people = User.objects.filter(is_staff=True).select_related("profile").order_by("pk")
    return render(request, "cms/users.html", _ctx(request, "users", form=form, people=people))


@owner_required
@require_POST
def user_toggle(request, pk):
    User = get_user_model()
    u = get_object_or_404(User, pk=pk)
    if u == request.user:
        messages.error(request, "You can't switch off your own account.")
    else:
        u.is_active = not u.is_active
        u.save(update_fields=["is_active"])
        messages.success(request, f"{u.username} is now {'active' if u.is_active else 'switched off'}.")
    return redirect("cms:users")
