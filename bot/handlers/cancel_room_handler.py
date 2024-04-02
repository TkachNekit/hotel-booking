from asgiref.sync import sync_to_async
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          MessageHandler, filters)

from bookings.views import cancel_user_booking, get_user_active_bookings
from users.views import get_user_by_telegram_id, is_authorized

END = ConversationHandler.END
IS_AUTHORIZED, HANDLE_BOOKING = range(2)


async def is_authorized_handle(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    if not await sync_to_async(is_authorized)(user_id):
        await update.message.reply_text("You have to be authorized to use this command",
                                        reply_markup=ReplyKeyboardRemove())
        return END

    await update.message.reply_text(
        "What booking do you want to cancel?", parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    user = await sync_to_async(get_user_by_telegram_id)(update.effective_user.id)
    user_bookings = await sync_to_async(get_user_active_bookings)(user)
    if not user_bookings:
        await update.message.reply_text(
            "User doesn't have any bookings?", parse_mode='Markdown',
        )
        return END

    button_lst = []
    button_ids = {}
    for i in range(len(user_bookings)):
        b = user_bookings[i]
        button = [b.__str__()]
        button_lst.append(button)
        button_ids[button[0]] = b.id

    context.user_data['buttons'] = button_ids
    await update.message.reply_text("Which booking?",
                                    reply_markup=ReplyKeyboardMarkup(button_lst, one_time_keyboard=True))
    return HANDLE_BOOKING


async def booking_cancel_handle(update: Update, context: CallbackContext) -> int:
    answer = update.message.text
    button_ids = context.user_data['buttons']

    if answer not in button_ids:
        await update.message.reply_text("Choose booking that you want to cancel")
        return IS_AUTHORIZED

    booking_id = button_ids[answer]
    user = await sync_to_async(get_user_by_telegram_id)(update.effective_user.id)

    await sync_to_async(cancel_user_booking)(user, booking_id)
    await update.message.reply_text("Booking was successfully canceled", reply_markup=ReplyKeyboardRemove())

    context.user_data.clear()
    return END


def cancel_booking_conversation() -> ConversationHandler:
    async def cancel_booking_start(update: Update, context: CallbackContext) -> int:
        await update.message.reply_text(
            "You will have to help me cancel your booking",
            reply_markup=ReplyKeyboardMarkup([['Okay']], one_time_keyboard=True))
        return IS_AUTHORIZED

    async def cancel(update: Update, context: CallbackContext) -> int:
        await update.message.reply_text("Canceling process was canceled", reply_markup=ReplyKeyboardRemove())
        context.user_data.clear()
        return END

    conv_handler_main = ConversationHandler(
        entry_points=[CommandHandler('cancel_booking', cancel_booking_start)],
        states={
            IS_AUTHORIZED: [MessageHandler(filters.TEXT & ~filters.COMMAND, is_authorized_handle)],
            HANDLE_BOOKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, booking_cancel_handle)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    return conv_handler_main
