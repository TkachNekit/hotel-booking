from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError


def validate_username(username: str) -> None:
    unicode_validator = UnicodeUsernameValidator()
    unicode_validator(username)


def validate_telegram_id(telegram_id: int) -> None:
    # Check if the value is a positive integer
    if not isinstance(telegram_id, int) or telegram_id <= 0:
        raise ValidationError("Telegram ID must be a positive integer.")

    # Example: Check if the Telegram ID has exactly 9 digits
    if len(str(telegram_id)) != 9:
        raise ValidationError("Telegram ID must be a 9-digit integer.")
