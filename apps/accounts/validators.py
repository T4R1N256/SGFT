"""Password rules for SGFT: the account password is the 6-digit admin PIN."""
from django.core.exceptions import ValidationError

from apps.accounts.models import is_pin


class SixDigitPasswordValidator:
    def validate(self, password, user=None):
        if not is_pin(password):
            raise ValidationError("La contraseña debe tener 6 dígitos.", code="password_not_six_digits")

    def get_help_text(self):
        return "La contraseña son 6 dígitos."