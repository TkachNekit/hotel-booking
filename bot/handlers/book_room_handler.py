from datetime import datetime

from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError
from django.http import Http404
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          MessageHandler, filters)

from bookings.views import book_room
from rooms.views import get_room_by_number
from users.views import get_user_by_telegram_id, is_authorized

END = ConversationHandler.END
IS_AUTHORIZED, ROOM_NUMBER, CHECKIN_DATE, CHECKOUT_DATE, SHOW_BOOKING_RESULT = range(5)


async def is_authorized_handle(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    if not await sync_to_async(is_authorized)(user_id):
        await update.message.reply_text("You have to be authorized to use this command",
                                        reply_markup=ReplyKeyboardRemove())
        return END

    await update.message.reply_text(
        "What room you want to book?\nEnter *room number* (for example: *111*)", parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    return ROOM_NUMBER


async def room_number_handler(update: Update, context: CallbackContext) -> int:
    try:
        room = await sync_to_async(get_room_by_number)(int(update.message.text))
        context.user_data['room'] = room

        await update.message.reply_text("Please, enter *check-in* date (YYYY-MM-DD):", parse_mode='Markdown')
        return CHECKIN_DATE

    except Http404 or ValueError:
        await update.message.reply_text(
            f"Room number *{update.message.text}* doesn't exist. Enter valid room number:", parse_mode='Markdown'
        )
        return ROOM_NUMBER


async def checkin_date_handler(update: Update, context: CallbackContext) -> int:
    try:
        checkin_date = datetime.strptime(update.message.text, '%Y-%m-%d').date()

        # Check if checkin_date >= today
        if checkin_date < datetime.now().date():
            await update.message.reply_text(
                "The check-in date cannot be earlier than today. Please choose another check-in date.",
                reply_markup=ReplyKeyboardRemove())
            return CHECKIN_DATE

        context.user_data['checkin_date'] = checkin_date
        await update.message.reply_text("Please, enter *check-out* date (YYYY-MM-DD):", parse_mode='Markdown',
                                        reply_markup=ReplyKeyboardRemove())
        return CHECKOUT_DATE
    except ValueError:
        await update.message.reply_text("Wrong date format. Please, enter date in format YYYY-MM-DD. "
                                        "(_2025-2-2_ for example)", parse_mode='Markdown',
                                        reply_markup=ReplyKeyboardRemove())
        return CHECKIN_DATE


async def checkout_date_handle(update: Update, context: CallbackContext) -> int:
    try:
        checkout_date = datetime.strptime(update.message.text, '%Y-%m-%d').date()
        checkin_date = context.user_data['checkin_date']

        # Check if checkin_date < checkout_date
        difference = checkout_date - checkin_date
        if difference.days < 1:
            await update.message.reply_text(
                "The *checkout* date cannot be earlier than 1 day after the *check-in* date.",
                parse_mode='Markdown')
            return CHECKOUT_DATE

        # Perform action with date filtering (use checkin_date and checkout_date)
        context.user_data['checkout_date'] = checkout_date

        await update.message.reply_text(
            f"Book room №{context.user_data['room'].number} on dates {checkin_date} - {checkout_date}?",
            reply_markup=ReplyKeyboardMarkup([['Yes', 'No']], one_time_keyboard=True)
        )
        return SHOW_BOOKING_RESULT
    except ValueError:
        await update.message.reply_text("Wrong date format. Please, enter date in format YYYY-MM-DD. "
                                        "(_2025-2-2_ for example)", parse_mode='Markdown',
                                        reply_markup=ReplyKeyboardRemove())

        return CHECKOUT_DATE


async def show_booking_result(update: Update, context: CallbackContext) -> int:
    answer = update.message.text
    try:
        assert answer.lower() == 'yes'

        user = await sync_to_async(get_user_by_telegram_id)(update.effective_user.id)
        room = context.user_data['room']
        checkin = context.user_data['checkin_date']
        checkout = context.user_data['checkout_date']

        await sync_to_async(book_room)(user=user, room_number=room.number, checkin_date=checkin, checkout_date=checkout)
        await update.message.reply_text(f"Room *№{room.number}* successfully booked on {checkin} - {checkout}",
                                        reply_markup=ReplyKeyboardRemove(), parse_mode='Markdown')
        context.user_data.clear()
        return END
    except AssertionError:
        await update.message.reply_text("Booking process canceled", reply_markup=ReplyKeyboardRemove())
        context.user_data.clear()
        return END
    except ValidationError as e:
        await update.message.reply_text(e.message, reply_markup=ReplyKeyboardRemove())
        context.user_data.clear()
        return END


def book_room_conversation() -> ConversationHandler:
    async def book_room_start(update: Update, context: CallbackContext) -> int:
        await update.message.reply_text(
            "You will have to help me find the best fit for you",
            reply_markup=ReplyKeyboardMarkup([['Okay']], one_time_keyboard=True))
        return IS_AUTHORIZED

    async def cancel(update: Update, context: CallbackContext) -> int:
        await update.message.reply_text("Booking process was canceled", reply_markup=ReplyKeyboardRemove())
        context.user_data.clear()
        return END

    conv_handler_main = ConversationHandler(
        entry_points=[CommandHandler('book_room', book_room_start)],
        states={
            IS_AUTHORIZED: [MessageHandler(filters.TEXT & ~filters.COMMAND, is_authorized_handle)],
            ROOM_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, room_number_handler)],
            CHECKIN_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, checkin_date_handler)],
            CHECKOUT_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, checkout_date_handle)],
            SHOW_BOOKING_RESULT: [MessageHandler(filters.TEXT & ~filters.COMMAND, show_booking_result)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    return conv_handler_main
