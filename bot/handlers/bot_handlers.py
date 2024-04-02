from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler

from bot.handlers.book_room_handler import book_room_conversation
from bot.handlers.cancel_room_handler import cancel_booking_conversation
from bot.handlers.login_conversation_handler import login_conversation
from bot.handlers.logout_conversation_handler import logout_conversation
from bot.handlers.register_conversation_handler import register_conversation
from bot.handlers.show_rooms_handler import show_rooms_conversation
from bot.handlers.telegram_messages import TELEGRAM_START_MESSAGE, COMMAND_CATALOG


def get_handlers() -> list:
    return [
        CommandHandler('start', start),
        CommandHandler('help', help),
        CallbackQueryHandler(button_click),
        show_rooms_conversation(),
        book_room_conversation(),
        cancel_booking_conversation(),
        login_conversation(),
        logout_conversation(),
        register_conversation()
    ]


# Defining a handler for responding to button clicks
async def button_click(update, context):
    query = update.callback_query
    if query.data == "support":
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(COMMAND_CATALOG, parse_mode='Markdown')


async def start(update: Update, context: ContextTypes):
    stroke = TELEGRAM_START_MESSAGE.format(update.effective_user.first_name)

    keyboard = [
        [InlineKeyboardButton("<<Show commands>>", callback_data="support")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(stroke, reply_markup=reply_markup, parse_mode='Markdown')


async def help(update: Update, context: ContextTypes):
    await update.message.reply_text(COMMAND_CATALOG, parse_mode='Markdown')
