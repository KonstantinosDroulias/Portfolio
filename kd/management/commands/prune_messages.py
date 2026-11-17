"""Delete contact messages older than 24 months (the privacy policy promises this). Runs nightly."""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from kd.models import ContactMessage


class Command(BaseCommand):
    def handle(self, *args, **opts):
        n, _ = ContactMessage.objects.filter(created_at__lt=timezone.now() - timedelta(days=730)).delete()
        self.stdout.write(f"Deleted {n} old messages")
