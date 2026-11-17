import re

from django.core.exceptions import ValidationError


class MixedCaseDigitValidator:
    """At least one uppercase letter, one lowercase letter and one number. Symbols are optional."""

    def validate(self, password, user=None):
        missing = []
        if not re.search(r"[A-ZΑ-ΩΆ-Ώ]", password):
            missing.append("one uppercase letter")
        if not re.search(r"[a-zα-ωά-ώ]", password):
            missing.append("one lowercase letter")
        if not re.search(r"\d", password):
            missing.append("one number")
        if missing:
            raise ValidationError("Your password needs " + ", ".join(missing) + ".", code="password_mixed")

    def get_help_text(self):
        return "Use at least one uppercase letter, one lowercase letter and one number."
