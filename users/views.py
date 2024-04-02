from django.contrib.auth.password_validation import validate_password

from users.models import User, TelegramAuthorization, TelegramUser

from django.contrib.auth.hashers import make_password, check_password

from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from validators import validate_username, validate_telegram_id


def register(first_name: str, last_name: str, username: str, email: str, password: str) -> None:
    # Validate email
    validate_email(email)
    if User.objects.filter(email=email).exists():
        raise ValidationError(f"User with \"{email}\" email already exists. Please enter a different email.")

    # Validate username
    validate_username(username)
    if User.objects.filter(username=username).exists():
        raise ValidationError(
            f"User with \"{username}\" username already exists. Please choose a different username."
        )

    # Validate password
    validate_password(password)

    # Hash the password
    hashed_password = make_password(password)

    # Create the user
    user = User.objects.create(
        first_name=first_name, last_name=last_name, username=username, email=email, password=hashed_password
    )


def is_username_unique(username: str) -> bool:
    if User.objects.filter(username=username).exists():
        return False
    return True


def is_email_unique(email: str) -> bool:
    if User.objects.filter(email=email).exists():
        return False
    return True


# telegram
def login_with_telegram(telegram_id: int, username: str, password: str) -> None:
    # User already logged in with this telegram acc
    if TelegramAuthorization.objects.filter(telegram_id=telegram_id).exists():
        raise ValidationError("Telegram user already logged in.")

    # Checks if user with given username exists
    if not User.objects.filter(username=username).exists():
        raise ValidationError(f"User with '{username}' username does not exist.")
    user = User.objects.get(username=username)

    # Validate telegram id
    validate_telegram_id(telegram_id)

    # Checks if given password matches hash in DB
    if not check_password(password, user.password):
        raise ValidationError("Passwords do not match.")

    # Creates link with telegram account and user
    authorization = TelegramAuthorization.objects.create(user=user, telegram_id=telegram_id)


# telegram
def logout_with_telegram(telegram_id: int) -> None:
    # Validate telegram id
    validate_telegram_id(telegram_id)

    # Checks if user with given telegram id logged in
    if not TelegramAuthorization.objects.filter(telegram_id=telegram_id).exists():
        raise ValidationError("User with given telegram id is not logged in.")

    # Deletes telegram-user link
    authorization = TelegramAuthorization.objects.get(telegram_id=telegram_id)
    authorization.delete()


def get_user_by_telegram_id(telegram_id: int) -> TelegramUser:
    # Validate telegram id
    validate_telegram_id(telegram_id)

    # Checks if user with given telegram id logged in
    if not TelegramAuthorization.objects.filter(telegram_id=telegram_id).exists():
        raise ValidationError("User with given telegram id is not logged in.")

    user = TelegramAuthorization.objects.get(telegram_id=telegram_id).user
    tg_user = TelegramUser(user)
    return tg_user


def is_authorized(telegram_id: int) -> bool:
    # Validate telegram id
    validate_telegram_id(telegram_id)

    return TelegramAuthorization.objects.filter(telegram_id=telegram_id).exists()
