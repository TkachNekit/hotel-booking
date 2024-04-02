from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          MessageHandler, filters)

from users.views import is_authorized, login_with_telegram

END = ConversationHandler.END
IS_AUTHORIZED, USERNAME, PASSWORD = range(3)


async def is_authorized_handle(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    if await sync_to_async(is_authorized)(user_id):
        await update.message.reply_text("You already authorized",
                                        reply_markup=ReplyKeyboardRemove())
        return END

    await update.message.reply_text(
        "Please, enter your *username*", parse_mode='Markdown', reply_markup=ReplyKeyboardRemove()
    )
    return USERNAME


async def username_handler(update: Update, context: CallbackContext) -> int:
    username = update.message.text
    context.user_data['username'] = username
    await update.message.reply_text(
        "Please, enter your *password*", parse_mode='Markdown', reply_markup=ReplyKeyboardRemove()
    )
    return PASSWORD


async def password_handler(update: Update, context: CallbackContext) -> int:
    try:
        password = update.message.text
        user_id = update.effective_user.id
        username = context.user_data['username']
        await sync_to_async(login_with_telegram)(user_id, username, password)
        await update.message.reply_text(
            f"You successfully logged in into {username}", parse_mode='Markdown', reply_markup=ReplyKeyboardRemove()
        )
        context.user_data.clear()
        return END
    except ValidationError as v:
        await update.message.reply_text(
            v.message, parse_mode='Markdown', reply_markup=ReplyKeyboardRemove()
        )
        context.user_data.clear()
        return END


def login_conversation() -> ConversationHandler:
    async def login_start(update: Update, context: CallbackContext) -> int:
        await update.message.reply_text(
            "You want to login in your account?",
            reply_markup=ReplyKeyboardMarkup([['Yes']], one_time_keyboard=True))
        return IS_AUTHORIZED

    async def cancel(update: Update, context: CallbackContext) -> int:
        await update.message.reply_text("Process was canceled", reply_markup=ReplyKeyboardRemove())
        context.user_data.clear()
        return END

    conv_handler_main = ConversationHandler(
        entry_points=[CommandHandler('login', login_start)],
        states={
            IS_AUTHORIZED: [MessageHandler(filters.TEXT & ~filters.COMMAND, is_authorized_handle)],
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, username_handler)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, password_handler)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    return conv_handler_main
