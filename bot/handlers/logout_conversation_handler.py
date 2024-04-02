from asgiref.sync import sync_to_async
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          MessageHandler, filters)

from users.views import is_authorized, logout_with_telegram

END = ConversationHandler.END
IS_AUTHORIZED, LOGOUT_CONFIRMATION, PASSWORD = range(3)


async def is_authorized_handle(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id

    if update.message.text.lower() != "yes":
        context.user_data.clear()
        return END

    if not await sync_to_async(is_authorized)(user_id):
        await update.message.reply_text("You are not authorized",
                                        reply_markup=ReplyKeyboardRemove())
        context.user_data.clear()
        return END

    await update.message.reply_text(
        "*You sure that you want to log out of your account?*", parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([['Yes'], ['No']], one_time_keyboard=True)
    )
    return LOGOUT_CONFIRMATION


async def logout_confirmation(update: Update, context: CallbackContext) -> int:
    answer = update.message.text
    if answer.lower() == 'yes':
        user_id = update.effective_user.id
        await sync_to_async(logout_with_telegram)(user_id)
        await update.message.reply_text(
            "You were logged out", parse_mode='Markdown', reply_markup=ReplyKeyboardRemove()
        )
    else:
        await update.message.reply_text(
            "You were *not* logged out", parse_mode='Markdown', reply_markup=ReplyKeyboardRemove()
        )
    context.user_data.clear()
    return END


def logout_conversation() -> ConversationHandler:
    async def logout_start(update: Update, context: CallbackContext) -> int:
        await update.message.reply_text(
            "You want to log out of your account?",
            reply_markup=ReplyKeyboardMarkup([['Yes'], ['No']], one_time_keyboard=True))
        return IS_AUTHORIZED

    async def cancel(update: Update, context: CallbackContext) -> int:
        await update.message.reply_text("Process was canceled", reply_markup=ReplyKeyboardRemove())
        context.user_data.clear()
        return END

    conv_handler_main = ConversationHandler(
        entry_points=[CommandHandler('logout', logout_start)],
        states={
            IS_AUTHORIZED: [MessageHandler(filters.TEXT & ~filters.COMMAND, is_authorized_handle)],
            LOGOUT_CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, logout_confirmation)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    return conv_handler_main
