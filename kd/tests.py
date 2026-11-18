import io
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from PIL import Image

from .models import ContactMessage, Post

MEDIA = tempfile.mkdtemp()


def png(name="x.png", size=(60, 40)):
    buf = io.BytesIO()
    Image.new("RGB", size, "#888").save(buf, "PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=MEDIA, NOINDEX_HOSTS=["preview.test"], ALLOWED_HOSTS=["*"],
                   CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
class SiteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_site", stdout=io.StringIO())
        cls.owner = get_user_model().objects.get(username="konstantinos")

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def test_public_pages(self):
        for url in ["/", "/writing/", "/work/", "/about/", "/contact/", "/feed/", "/sitemap.xml", "/robots.txt",
                    "/writing/topic/e-commerce/", "/writing/tag/django/", "/writing/?q=plugin",
                    "/writing/one-system-behind-every-store/", "/privacy/", "/llms.txt", "/llms-full.txt"]:
            r = self.client.get(url)
            self.assertEqual(r.status_code, 200, url)
        self.assertEqual(self.client.get("/nope/").status_code, 404)
        home = self.client.get("/").content.decode()
        self.assertIn('rel="canonical"', home)
        self.assertIn('"@type": "Person"', home)
        self.assertNotIn("/admin", home)  # no admin link for visitors
        post = self.client.get("/writing/one-system-behind-every-store/").content.decode()
        self.assertIn("BlogPosting", post)
        self.assertIn('og:type" content="article"', post)
        self.assertNotIn("adminbar", post)
        self.assertIn("https://konstantinosdroulias.com/sitemap.xml", self.client.get("/robots.txt").content.decode())
        self.assertIn("https://konstantinosdroulias.com/writing/", self.client.get("/sitemap.xml").content.decode())
        llms = self.client.get("/llms.txt").content.decode()
        self.assertTrue(llms.startswith("# Konstantinos Droulias"))
        self.assertIn("/writing/one-system-behind-every-store/", llms)
        self.assertIn("## The hub", self.client.get("/llms-full.txt").content.decode())
        robots = self.client.get("/robots.txt").content.decode()
        self.assertIn("User-agent: GPTBot", robots)
        self.assertIn("User-agent: ClaudeBot", robots)
        self.assertIn('id="consent"', home)
        self.assertIn('popovertarget="a11y"', home)

    def test_preview_host_is_noindex(self):
        r = self.client.get("/", HTTP_HOST="preview.test")
        self.assertEqual(r["X-Robots-Tag"], "noindex, nofollow")
        self.assertIn("Disallow: /", self.client.get("/robots.txt", HTTP_HOST="preview.test").content.decode())

    def test_contact(self):
        r = self.client.post("/contact/", {"name": "A", "email": "a@example.com", "topic": "Website", "message": "Hi"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(ContactMessage.objects.count(), 1)
        self.assertIn("Message sent", self.client.get(r["Location"]).content.decode())
        self.client.post("/contact/", {"name": "B", "email": "b@example.com", "topic": "Website", "message": "x", "website": "spam"})
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_cms_requires_login(self):
        r = self.client.get("/admin/posts/")
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r["Location"].startswith("/admin/login/"))
        self.assertEqual(self.client.get("/admin/login/").status_code, 200)

    def test_cms_flow(self):
        self.client.force_login(self.owner)
        for url in ["/admin/", "/admin/posts/", "/admin/posts/new/", "/admin/messages/", "/admin/settings/",
                    "/admin/profile/", "/admin/users/"]:
            self.assertEqual(self.client.get(url).status_code, 200, url)
        # adminbar + edit button on a post
        p = Post.objects.first()
        html = self.client.get(p.get_absolute_url()).content.decode()
        self.assertIn("Admin panel", html)
        self.assertIn(f"/admin/posts/{p.pk}/", html)
        self.assertIn("konstantinos", html)
        # create a draft with cover
        r = self.client.post("/admin/posts/new/", {
            "title": "Hello there", "excerpt": "Short", "body": "## Hi\n\n![a](/x.png \"Cap\")", "status": "draft",
            "published_at": "2026-11-18T10:00", "tags_text": "Go, Django", "new_category": "Notes", "cover": png(),
            "author": self.owner.pk})
        self.assertEqual(r.status_code, 302, r.content[:2000])
        post = Post.objects.get(slug="hello-there")
        self.assertEqual(post.status, "draft")
        self.assertTrue(post.cover)
        self.assertIn("<figcaption>Cap</figcaption>", post.body_html)
        self.assertEqual(self.client.get(post.get_absolute_url()).status_code, 200)  # owner sees draft
        # upload + preview
        r = self.client.post("/admin/upload/", {"file": png("y.png")})
        self.assertIn("url", r.json())
        self.assertIn("<h2", self.client.post("/admin/preview/", {"body": "## x"}).json()["html"])
        # settings + CV
        r = self.client.post("/admin/settings/", {"upload_cv": "1", "cv": SimpleUploadedFile("cv.pdf", b"%PDF-1.4 test", content_type="application/pdf")})
        self.assertEqual(r.status_code, 302)
        # add a writer, who can only see own posts
        r = self.client.post("/admin/users/", {"username": "writer", "password": "Long-pass-123", "display_name": "W"})
        self.assertEqual(r.status_code, 302)
        self.client.logout()
        writer = get_user_model().objects.get(username="writer")
        self.client.force_login(writer)
        self.assertEqual(self.client.get(f"/admin/posts/{post.pk}/").status_code, 404)
        self.assertEqual(self.client.get("/admin/settings/").status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(post.get_absolute_url()).status_code, 404)  # public can't see draft
        # profile photo crop
        self.client.force_login(self.owner)
        r = self.client.post("/admin/profile/", {"p-display_name": "K D", "p-new_photo": png("me.png", (300, 400))})
        self.assertEqual(r.status_code, 302)
        self.owner.profile.refresh_from_db()
        self.assertTrue(self.owner.profile.avatar.name.endswith(".webp"))

    def test_login(self):
        self.owner.set_password("right-password-1")
        self.owner.save()
        r = self.client.post("/admin/login/", {"username": "konstantinos", "password": "nope"})
        self.assertContains(r, "Wrong username or password")
        r = self.client.post("/admin/login/", {"username": "konstantinos", "password": "right-password-1", "next": "/admin/posts/"})
        self.assertEqual(r["Location"], "/admin/posts/")



class PasswordRuleTests(TestCase):
    def test_rules(self):
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError
        validate_password("Smyrni26")  # 8 chars, upper, lower, number, no symbol: fine
        for bad in ["Smyrni2", "smyrni26", "SMYRNI26", "Smyrnios"]:
            with self.assertRaises(ValidationError, msg=bad):
                validate_password(bad)


class WorkAndProjectsTests(TestCase):
    def test_work_timeline_and_projects_page(self):
        from .models import Project
        r = self.client.get("/work/")
        self.assertContains(r, "Lead developer")
        self.assertNotContains(r, "StickerPro")
        self.assertNotContains(r, "Movie Recommender")
        Project.objects.create(title="Hidden one", summary="x", published=False)
        r = self.client.get("/projects/")
        self.assertContains(r, "Movie Recommender")
        self.assertContains(r, "scikit-learn")
        self.assertNotContains(r, "Hidden one")
        self.assertContains(self.client.get("/llms.txt"), "## Projects")


class ProjectCmsTests(TestCase):
    def test_owner_adds_and_edits_project(self):
        from .models import Project
        u = get_user_model().objects.create_superuser("owner", "o@example.com", "Passw0rdx")
        self.client.force_login(u)
        self.assertContains(self.client.get("/admin/projects/"), "Movie Recommender")
        self.assertContains(self.client.get("/admin/projects/new/"), "Add project")
        r = self.client.post("/admin/projects/new/", {"title": "Quick Notes", "kind": "Web app", "year": "2026",
                                                       "summary": "A note pad.", "stack": "Go", "url": "", "link_label": "",
                                                       "order": 5, "published": "on"})
        p = Project.objects.get(title="Quick Notes")
        self.assertRedirects(r, f"/admin/projects/{p.pk}/")
        self.assertContains(self.client.get("/projects/"), "Quick Notes")
        self.client.post(f"/admin/projects/{p.pk}/delete/")
        self.assertFalse(Project.objects.filter(pk=p.pk).exists())
