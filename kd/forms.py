from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.text import slugify

from .models import Category, Post, Profile, Project, SiteSettings, Tag

TOPICS = [("Website", "Website"), ("E-shop", "E-shop"), ("Business system", "Business system"), ("Something else", "Something else")]


class ContactForm(forms.Form):
    name = forms.CharField(max_length=120)
    email = forms.EmailField()
    topic = forms.ChoiceField(choices=TOPICS, initial="Website", widget=forms.RadioSelect)
    message = forms.CharField(max_length=5000, widget=forms.Textarea(attrs={"rows": 6}))
    website = forms.CharField(required=False)  # honeypot


class PostForm(forms.ModelForm):
    tags_text = forms.CharField(label="Tags", required=False, help_text="Comma separated")
    new_category = forms.CharField(label="New topic", required=False, max_length=60)
    remove_cover = forms.BooleanField(required=False)

    class Meta:
        model = Post
        fields = ["title", "slug", "excerpt", "body", "cover", "cover_alt", "category", "status",
                  "published_at", "seo_title", "seo_description", "author"]
        widgets = {
            "excerpt": forms.Textarea(attrs={"rows": 3}),
            "body": forms.Textarea(attrs={"rows": 28, "spellcheck": "true"}),
            "published_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "cover": forms.FileInput(attrs={"accept": "image/*"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False
        self.fields["slug"].help_text = "Leave empty to make it from the title"
        self.fields["category"].label = "Topic"
        self.fields["category"].empty_label = "No topic"
        self.fields["published_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        User = get_user_model()
        self.fields["author"].queryset = User.objects.filter(is_staff=True, is_active=True)
        self.fields["author"].label_from_instance = lambda u: u.profile.name
        if user and not user.is_superuser:
            del self.fields["author"]
        if self.instance.pk:
            self.fields["tags_text"].initial = ", ".join(t.name for t in self.instance.tags.all())

    def clean_slug(self):
        slug = slugify(self.cleaned_data.get("slug") or self.cleaned_data.get("title") or "")[:200]
        if not slug:
            slug = "post"
        base, n = slug, 2
        while Post.objects.filter(slug=slug).exclude(pk=self.instance.pk).exists():
            slug = f"{base}-{n}"
            n += 1
        return slug

    def save(self, commit=True):
        post = super().save(commit=False)
        if self.cleaned_data.get("remove_cover") and post.cover:
            post.cover.delete(save=False)
            post.cover = ""
        name = self.cleaned_data.get("new_category", "").strip()
        if name:
            cat = Category.objects.filter(name__iexact=name).first() or Category.objects.create(name=name, slug=slugify(name))
            post.category = cat
        post.save()
        names = [t.strip() for t in self.cleaned_data.get("tags_text", "").split(",") if t.strip()]
        tags = []
        for n in names:
            tag = Tag.objects.filter(name__iexact=n).first() or Tag.objects.create(name=n, slug=slugify(n) or n.lower())
            tags.append(tag)
        post.tags.set(tags)
        return post


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = ["email", "notify_email", "based_in", "currently", "agency_name", "agency_url",
                  "github", "linkedin", "instagram", "x", "now_items", "now_updated", "analytics_id"]
        widgets = {"now_items": forms.Textarea(attrs={"rows": 6}),
                   "now_updated": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}


    def clean_analytics_id(self):
        import re
        v = self.cleaned_data["analytics_id"].strip().upper()
        if v and not re.fullmatch(r"G-[A-Z0-9]{4,16}", v):
            raise forms.ValidationError("Use the GA4 measurement ID, like G-ABC123XYZ.")
        return v


class CVForm(forms.Form):
    cv = forms.FileField(label="CV (PDF)")

    def clean_cv(self):
        f = self.cleaned_data["cv"]
        if not f.name.lower().endswith(".pdf") or f.read(5) != b"%PDF-":
            raise forms.ValidationError("Upload a PDF file.")
        f.seek(0)
        if f.size > 10 * 1024 * 1024:
            raise forms.ValidationError("Keep it under 10 MB.")
        return f


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    new_photo = forms.ImageField(label="Photo", required=False,
                                 help_text="A cut-out PNG/WebP works best. Your face is cropped for the avatar.")

    class Meta:
        model = Profile
        fields = ["display_name", "role_line", "bio", "github", "linkedin", "instagram"]
        widgets = {"bio": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        u = self.instance.user
        self.fields["first_name"].initial = u.first_name
        self.fields["last_name"].initial = u.last_name
        self.fields["email"].initial = u.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        u = profile.user
        u.first_name = self.cleaned_data["first_name"]
        u.last_name = self.cleaned_data["last_name"]
        u.email = self.cleaned_data["email"]
        u.save()
        if self.cleaned_data.get("new_photo"):
            profile.set_photo(self.cleaned_data["new_photo"])
        profile.save()
        return profile


class NewUserForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField(required=False)
    display_name = forms.CharField(max_length=120, required=False)
    password = forms.CharField(widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    is_superuser = forms.BooleanField(label="Full access (can manage users and settings)", required=False)

    def clean_username(self):
        name = self.cleaned_data["username"].strip()
        if get_user_model().objects.filter(username__iexact=name).exists():
            raise forms.ValidationError("That username is taken.")
        return name

    def clean_password(self):
        pw = self.cleaned_data["password"]
        validate_password(pw)
        return pw


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["title", "kind", "year", "summary", "stack", "url", "link_label", "order", "published"]
        widgets = {"summary": forms.Textarea(attrs={"rows": 4})}
