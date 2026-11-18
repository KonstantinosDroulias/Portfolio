from django.db import migrations, models


SEED = [
    {"title": "Movie Recommender", "kind": "Machine learning", "year": "2026", "order": 10,
     "summary": "A movie recommendation app with my own item-based collaborative-filtering model trained on 100k "
                "MovieLens ratings, served through a REST API to a React front end.",
     "stack": "Django, DRF, React, scikit-learn, Docker, Nginx, PostgreSQL",
     "url": "https://github.com/KonstantinosDroulias/movie-recomender", "link_label": "GitHub"},
    {"title": "Office check-in", "kind": "Web app", "year": "2026", "order": 20,
     "summary": "An NFC check-in web app for the shared office I work from with two friends: tap the tag at the door "
                "and it logs who is in.",
     "stack": "Flask, SQLite, NFC", "url": "", "link_label": "Private"},
]


def seed(apps, schema_editor):
    Project = apps.get_model("kd", "Project")
    for row in SEED:
        Project.objects.create(**row)


class Migration(migrations.Migration):
    dependencies = [("kd", "0002_analytics_id")]

    operations = [
        migrations.CreateModel(
            name="Project",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=120)),
                ("kind", models.CharField(blank=True, help_text="Short label, like “Machine learning” or “Web app”", max_length=60, verbose_name="Type")),
                ("year", models.CharField(blank=True, help_text="Like 2026 or 2025 — 2026", max_length=20)),
                ("summary", models.TextField(help_text="Two or three sentences: what it is, what you built it with", max_length=600)),
                ("stack", models.CharField(blank=True, help_text="Comma separated, like Django, React, Docker", max_length=200)),
                ("url", models.URLField(blank=True, verbose_name="Link")),
                ("link_label", models.CharField(blank=True, help_text="Shown instead of the address, like GitHub or Live site", max_length=80)),
                ("order", models.PositiveIntegerField(default=0, help_text="Lower numbers show first")),
                ("published", models.BooleanField(default=True, verbose_name="Show on the site")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["order", "-created_at"]},
        ),
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
