from datetime import datetime

from asgiref.sync import sync_to_async
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          MessageHandler, filters)

from rooms.views import SortType, get_available_rooms

END = ConversationHandler.END
CONV_DATE, CONV_COST, CONV_CAPACITY, CONV_SORT = range(4)
DATE_START, CHECKIN_DATE, CHECKOUT_DATE = range(4, 7)
COST_START, MIN_COST, MAX_COST = range(7, 10)
CAPACITY_START, MIN_CAPACITY = range(10, 12)
SORT_START, SORT_TYPE_CHOOSING = range(12, 14)
SHOW_CHOSEN_ROOMS = 14


# Show available rooms conversation
def get_date_conversation() -> ConversationHandler:
    # Conversation states

    async def start_date_filter(update, context):
        reply_keyboard = [['Yes', 'No']]
        await update.message.reply_text(
            "Will there be filtering by specific dates? *(Yes | No)*", parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
        return DATE_START

    async def yes_or_no_handler(update, context):
        user_choice = update.message.text
        if user_choice.lower() == 'yes':
            await update.message.reply_text("Please, enter *check-in* date (YYYY-MM-DD):", parse_mode='Markdown')
            return CHECKIN_DATE
        else:
            await update.message.reply_text("No filter by dates", reply_markup=ReplyKeyboardRemove())
            context.user_data['checkin_date'] = None
            context.user_data['checkout_date'] = None

            await update.message.reply_text(
                "Will there be filter by min and max cost for one night?",
                reply_markup=ReplyKeyboardMarkup([['Yes', 'No']], one_time_keyboard=True)
            )
            return END

    async def handle_checkin_date(update, context):
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

    async def handle_checkout_date(update, context):
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
                "Will there be filter by min and max cost for one night?",
                reply_markup=ReplyKeyboardMarkup([['Yes', 'No']], one_time_keyboard=True)
            )
            return END
        except ValueError:
            await update.message.reply_text("Wrong date format. Please, enter date in format YYYY-MM-DD. "
                                            "(_2025-2-2_ for example)", parse_mode='Markdown',
                                            reply_markup=ReplyKeyboardRemove())

            return CHECKOUT_DATE

    async def cancel(update, context):
        await update.message.reply_text("No filter by dates", reply_markup=ReplyKeyboardRemove())
        await update.message.reply_text(
            "Will there be filter by min and max cost for one night?",
            reply_markup=ReplyKeyboardMarkup([['Yes', 'No']], one_time_keyboard=True)
        )
        context.user_data['checkin_date'] = None
        context.user_data['checkout_date'] = None
        return END

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, start_date_filter)],
        states={
            DATE_START: [MessageHandler(filters.Regex('^(Yes|No)$'), yes_or_no_handler)],
            CHECKIN_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_checkin_date)],
            CHECKOUT_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_checkout_date)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        map_to_parent={
            END: CONV_COST
        }
    )

    return conv_handler


def get_cost_conversation() -> ConversationHandler:
    async def start_cost_filter(update: Update, context: CallbackContext) -> int:
        user_choice = update.message.text
        if user_choice.lower() == 'yes':
            await update.message.reply_text("Please, enter *min* cost for one night:",
                                            parse_mode='Markdown',
                                            reply_markup=ReplyKeyboardRemove())
            return MIN_COST
        else:
            await update.message.reply_text("No filter by cost", reply_markup=ReplyKeyboardRemove())
            context.user_data['min_cost'] = None
            context.user_data['max_cost'] = None

            await update.message.reply_text(
                "Will there be filter by room capacity?",
                reply_markup=ReplyKeyboardMarkup([['Yes', 'No']], one_time_keyboard=True)
            )

            return END

    async def handle_min_cost(update: Update, context: CallbackContext) -> int:
        try:
            min_cost = float(update.message.text)

            # Check if min_cost >= 0
            if min_cost < 0:
                await update.message.reply_text("Minimum cost cannot be negative. Please enter a positive number.",
                                                reply_markup=ReplyKeyboardRemove())
                return MIN_COST

            context.user_data['min_cost'] = min_cost
            await update.message.reply_text("Please, enter *max* cost for one night:",
                                            parse_mode='Markdown', reply_markup=ReplyKeyboardRemove())
            return MAX_COST
        except ValueError:
            await update.message.reply_text("Wrong cost format. Enter number please",
                                            reply_markup=ReplyKeyboardRemove())
            return MIN_COST

    async def handle_max_cost(update: Update, context: CallbackContext) -> int:
        try:
            max_cost = float(update.message.text)

            # Check if max_cost >= min_cost
            if max_cost < context.user_data['min_cost']:
                await update.message.reply_text(
                    "The maximum cost cannot be less than the minimum. "
                    "Please enter a number greater than or equal to the minimum cost.")
                return MAX_COST

            context.user_data['max_cost'] = max_cost

            await update.message.reply_text(
                "Will there be filter by room capacity?",
                reply_markup=ReplyKeyboardMarkup([['Yes', 'No']], one_time_keyboard=True)
            )

            return END
        except ValueError:
            await update.message.reply_text("Wrong cost format. Enter number please",
                                            reply_markup=ReplyKeyboardRemove())
            return MAX_COST

    async def cancel(update: Update, context: CallbackContext) -> int:
        await update.message.reply_text("No filter by cost", reply_markup=ReplyKeyboardRemove())
        context.user_data['min_cost'] = None
        context.user_data['max_cost'] = None

        await update.message.reply_text(
            "Will there be filter by room capacity?",
            reply_markup=ReplyKeyboardMarkup([['Yes', 'No']], one_time_keyboard=True)
        )

        return END

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^(Yes|No)$'), start_cost_filter)],
        states={
            COST_START: [MessageHandler(filters.Regex('^(Yes|No)$'), start_cost_filter)],
            MIN_COST: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_min_cost)],
            MAX_COST: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_max_cost)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        map_to_parent={
            END: CONV_CAPACITY
        }
    )

    return conv_handler


def get_capacity_conversation():
    async def start_capacity_filter(update: Update, context: CallbackContext) -> int:
        user_choice = update.message.text
        if user_choice.lower() == 'yes':
            await update.message.reply_text("Please, enter minimal capacity for a room:",
                                            reply_markup=ReplyKeyboardRemove())
            return MIN_CAPACITY
        else:
            await update.message.reply_text("No filter by capacity",
                                            reply_markup=ReplyKeyboardRemove())
            context.user_data['min_capacity'] = None

            await update.message.reply_text(
                "Will sort be needed?",
                reply_markup=ReplyKeyboardMarkup([['Yes', 'No']], one_time_keyboard=True)
            )

            return END

    async def handle_min_capacity(update: Update, context: CallbackContext) -> int:
        try:
            min_capacity = int(update.message.text)

            # Check if max_cost >= min_cost
            if min_capacity < 1:
                await update.message.reply_text("Capacity can't be < 1.")
                return MIN_CAPACITY

            context.user_data['min_capacity'] = min_capacity

            await update.message.reply_text(
                "Will sort be needed?",
                reply_markup=ReplyKeyboardMarkup([['Yes', 'No']], one_time_keyboard=True)
            )

            return END
        except ValueError:
            await update.message.reply_text("Wrong format for a capacity. Please enter number.")
            return MIN_CAPACITY

    async def cancel(update: Update, context: CallbackContext) -> int:
        await update.message.reply_text("No filter by capacity", reply_markup=ReplyKeyboardRemove())
        context.user_data['min_capacity'] = None

        await update.message.reply_text(
            "Will sort be needed?",
            reply_markup=ReplyKeyboardMarkup([['Yes', 'No']], one_time_keyboard=True)
        )

        return END

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^(Yes|No)$'), start_capacity_filter)],
        states={
            CAPACITY_START: [MessageHandler(filters.Regex('^(Yes|No)$'), start_capacity_filter)],
            MIN_CAPACITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_min_capacity)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        map_to_parent={
            END: CONV_SORT
        }
    )
    return conv_handler


def get_sort_conversation() -> ConversationHandler:
    sort_keyboard_list = [
        ['No sort', 'Cost descending', 'Cost ascending', 'Capacity descending',
         'Capacity ascending']
    ]

    async def start_sort(update: Update, context: CallbackContext) -> int:
        user_choice = update.message.text
        if user_choice.lower() == 'yes':
            await update.message.reply_text("Please, choose sort type",
                                            reply_markup=ReplyKeyboardMarkup(sort_keyboard_list,
                                                                             one_time_keyboard=True))
            return SORT_TYPE_CHOOSING
        else:
            await update.message.reply_text("No sort", reply_markup=ReplyKeyboardRemove())
            context.user_data['sort_type'] = SortType.NONE

            await update.message.reply_text("Show available rooms?",
                                            reply_markup=ReplyKeyboardMarkup([['Show']], one_time_keyboard=True))

            return END

    async def handle_sort_type(update: Update, context: CallbackContext) -> int:
        try:
            user_choice = update.message.text
            if user_choice.lower() == 'no sort':
                context.user_data['sort_type'] = SortType.NONE
            elif user_choice.lower() == 'cost descending':
                context.user_data['sort_type'] = SortType.COST_DESCENDING
            elif user_choice.lower() == 'cost ascending':
                context.user_data['sort_type'] = SortType.COST_ASCENDING
            elif user_choice.lower() == 'capacity descending':
                context.user_data['sort_type'] = SortType.CAPACITY_DESCENDING
            elif user_choice.lower() == 'capacity ascending':
                context.user_data['sort_type'] = SortType.CAPACITY_ASCENDING
            else:
                await update.message.reply_text("Please, choose sort type",
                                                reply_markup=ReplyKeyboardMarkup(sort_keyboard_list,
                                                                                 one_time_keyboard=True))
                return SORT_TYPE_CHOOSING

            await update.message.reply_text("Show available rooms?",
                                            reply_markup=ReplyKeyboardMarkup([['Show']], one_time_keyboard=True))

            return END
        except ValueError:
            await update.message.reply_text("Please, choose sort type",
                                            reply_markup=ReplyKeyboardMarkup(sort_keyboard_list,
                                                                             one_time_keyboard=True))
            return SORT_TYPE_CHOOSING

    async def cancel(update: Update, context: CallbackContext) -> int:
        await update.message.reply_text("No sort", reply_markup=ReplyKeyboardRemove())
        context.user_data['sort_type'] = SortType.NONE

        await update.message.reply_text("Show available rooms?",
                                        reply_markup=ReplyKeyboardMarkup([['Show']], one_time_keyboard=True))

        return END

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^(Yes|No)$'), start_sort)],
        states={
            SORT_START: [MessageHandler(filters.Regex('^(Yes|No)$'), start_sort)],
            SORT_TYPE_CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sort_type)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        map_to_parent={
            END: SHOW_CHOSEN_ROOMS
        }
    )
    return conv_handler


def get_chosen_rooms():
    async def get_room_list(update: Update, context: CallbackContext) -> int:
        room_list = await sync_to_async(get_available_rooms)(checkin_date=context.user_data['checkin_date'],
                                                             checkout_date=context.user_data['checkout_date'],
                                                             min_cost=context.user_data['min_cost'],
                                                             max_cost=context.user_data['max_cost'],
                                                             min_capacity=context.user_data['min_capacity'],
                                                             sort_type=context.user_data['sort_type'].value,
                                                             )

        if not room_list:
            await update.message.reply_text("No available rooms =(")
        else:
            output_stroke = ""
            i = 0
            while i != len(room_list):
                room = room_list[i]
                temp_stroke = output_stroke + room.__str__() + '\n\n'
                if len(temp_stroke) > 4096:
                    await update.message.reply_text(output_stroke)
                    output_stroke = ""
                else:
                    output_stroke = temp_stroke
                    i += 1
            await update.message.reply_text(output_stroke, reply_markup=ReplyKeyboardRemove())
        return END

    return MessageHandler(filters.TEXT & ~filters.COMMAND, get_room_list)


def show_rooms_conversation() -> ConversationHandler:
    async def show_available_rooms(update: Update, context: CallbackContext) -> int:
        await update.message.reply_text(
            "Filters and sorting options will be provided to help you choose the desired room.",
            reply_markup=ReplyKeyboardMarkup([['Okay']], one_time_keyboard=True))
        return CONV_DATE

    async def cancel(update: Update, context: CallbackContext) -> int:
        await update.message.reply_text("No room list, as you wish", reply_markup=ReplyKeyboardRemove())
        context.user_data.clear()
        return END

    conv_handler_date = get_date_conversation()
    conv_handler_cost = get_cost_conversation()
    conv_handler_capacity = get_capacity_conversation()
    conv_handler_sort = get_sort_conversation()

    show_chosen_rooms = get_chosen_rooms()

    conv_handler_main = ConversationHandler(
        entry_points=[CommandHandler('show_available_rooms', show_available_rooms)],
        states={
            CONV_DATE: [conv_handler_date],
            CONV_COST: [conv_handler_cost],
            CONV_CAPACITY: [conv_handler_capacity],
            CONV_SORT: [conv_handler_sort],
            SHOW_CHOSEN_ROOMS: [show_chosen_rooms],
            END: [cancel]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    return conv_handler_main
