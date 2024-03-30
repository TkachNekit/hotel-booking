from users.models import User


# telegram
def login(telegram_id: int, username: str, password: str) -> None:
    pass


# telegram
def logout(telegram_id: int) -> None:
    pass


def register(first_name: str, last_name: str, username: str, email: str, password: str) -> None:
    pass


def get_user_by_telegram_id(telegram_id: int) -> User:
    pass


def is_authorized(telegram_id: int) -> bool:
    pass
