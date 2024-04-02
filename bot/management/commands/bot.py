import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from telegram.error import InvalidToken

from bot.bot import Bot

log_level = logging.INFO if settings.DEBUG else logging.WARNING

# Configure root logger
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=log_level
)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        try:
            _BOT_TOKEN = settings.BOT_TOKEN
            logging.info("Obtained token successfully")
            bot = Bot(_BOT_TOKEN)
            bot.run_polling()
        except InvalidToken:
            logging.critical("Error occurred while obtaining Bot token from environment")
