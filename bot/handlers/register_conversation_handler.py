from asgiref.sync import sync_to_async
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.error import NetworkError
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          MessageHandler, filters)

from users.views import (is_authorized, is_email_unique, is_username_unique,
                         register)
from validators import validate_username

END = ConversationHandler.END
IS_AUTHORIZED, FIRST_NAME, LAST_NAME, USERNAME, EMAIL, PASSWORD1, PASSWORD2, REGISTRATION = range(8)


async def is_authorized_handle(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id

    if update.message.text.lower() != "yes":
        context.user_data.clear()
        return END

    if await sync_to_async(is_authorized)(user_id):
        await update.message.reply_text("You already authorized",
                                        reply_markup=ReplyKeyboardRemove())
        return END

    await update.message.reply_text(
        "Please, enter your *FIRST NAME*:", parse_mode='Markdown', reply_markup=ReplyKeyboardRemove()
    )
    return FIRST_NAME


async def first_name_handle(update: Update, context: CallbackContext) -> int:
    first_name = update.message.text
    if len(first_name) > 128:
        await update.message.reply_text("First name can be only 128 symbols long", parse_mode='Markdown')
        await update.message.reply_text("Please, enter your *FIRST NAME*:", parse_mode='Markdown')
        return FIRST_NAME
    context.user_data['first_name'] = first_name

    await update.message.reply_text(
        "Please, enter your *LAST NAME*:", parse_mode='Markdown', reply_markup=ReplyKeyboardRemove()
    )

    return LAST_NAME


async def last_name_handle(update: Update, context: CallbackContext) -> int:
    last_name = update.message.text
    if len(last_name) > 128:
        await update.message.reply_text("Last name can be only 128 symbols long", parse_mode='Markdown')
        await update.message.reply_text("Please, enter your *LAST NAME*:", parse_mode='Markdown')
        return LAST_NAME
    context.user_data['last_name'] = last_name

    await update.message.reply_text(
        "Please, enter your *USERNAME*:", parse_mode='Markdown', reply_markup=ReplyKeyboardRemove()
    )

    return USERNAME


async def registration_username_handle(update: Update, context: CallbackContext) -> int:
    try:
        username = update.message.text

        if len(username) > 128:
            raise ValidationError("Username can be only 128 symbols long")

        validate_username(username)

        if not await sync_to_async(is_username_unique)(username):
            raise ValidationError("This username is already registered in system")

        context.user_data['username'] = username

        await update.message.reply_text(
            "Please, enter your *EMAIL*", parse_mode='Markdown', reply_markup=ReplyKeyboardRemove()
        )
        return EMAIL
    except ValidationError as v:
        await update.message.reply_text(v.message, parse_mode='Markdown')
        await update.message.reply_text(
            "Please, enter your *USERNAME*:", parse_mode='Markdown', reply_markup=ReplyKeyboardRemove()
        )
        return USERNAME


async def email_handle(update: Update, context: CallbackContext) -> int:
    try:
        email = update.message.text

        validate_email(email)
        if not await sync_to_async(is_email_unique)(email):
            raise ValidationError("This email is already registered in system")

        context.user_data['email'] = email

        await update.message.reply_text(
            "Please, enter your *PASSWORD*", parse_mode='Markdown', reply_markup=ReplyKeyboardRemove()
        )
        return PASSWORD1
    except ValidationError as e:
        for m in e.messages:
            await update.message.reply_text(m, parse_mode='Markdown')
        await update.message.reply_text(
            "Please, enter your *EMAIL*:", parse_mode='Markdown', reply_markup=ReplyKeyboardRemove()
        )
        return EMAIL
    except NetworkError:
        await update.message.reply_text("This email is incorrect.", parse_mode='Markdown')
        await update.message.reply_text(
            "Please, enter your *EMAIL*:", parse_mode='Markdown', reply_markup=ReplyKeyboardRemove()
        )
        return EMAIL


async def password1_handle(update: Update, context: CallbackContext) -> int:
    try:
        password = update.message.text

        validate_password(password)

        context.user_data['password1'] = make_password(password)

        await update.message.reply_text(
            "Please, enter your *password* again", parse_mode='Markdown', reply_markup=ReplyKeyboardRemove()
        )
        return PASSWORD2

    except ValidationError as v:
        for m in v.messages:
            await update.message.reply_text(m, parse_mode='Markdown')
        await update.message.reply_text("Please, enter your *password*", parse_mode='Markdown')
        return PASSWORD1


async def password2_handle(update: Update, context: CallbackContext) -> int:
    try:
        password = update.message.text

        hashed_password = context.user_data['password1']
        if not check_password(password, hashed_password):
            await update.message.reply_text(
                "Password doesn't match. Please, enter your *password*", parse_mode='Markdown',
            )
            return PASSWORD1

        first_name = context.user_data['first_name']
        last_name = context.user_data['last_name']
        username = context.user_data['username']
        email = context.user_data['email']

        await sync_to_async(register)(first_name, last_name, username, email, password)

        await update.message.reply_text(
            f"User *{username}* was successfully registered. You can log in!", parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data.clear()
        return END

    except ValidationError as v:
        for m in v.messages:
            await update.message.reply_text(m, parse_mode='Markdown')
        await update.message.reply_text(
            "Please, enter your *password*", parse_mode='Markdown', reply_markup=ReplyKeyboardRemove()
        )
        return PASSWORD1


def register_conversation() -> ConversationHandler:
    async def registration_start(update: Update, context: CallbackContext) -> int:
        await update.message.reply_text(
            "You want to register new account?",
            reply_markup=ReplyKeyboardMarkup([['Yes'], ['No']], one_time_keyboard=True))
        return IS_AUTHORIZED

    async def cancel(update: Update, context: CallbackContext) -> int:
        await update.message.reply_text("Registration was canceled", reply_markup=ReplyKeyboardRemove())
        context.user_data.clear()
        return END

    conv_handler_main = ConversationHandler(
        entry_points=[CommandHandler('register', registration_start)],
        states={
            IS_AUTHORIZED: [MessageHandler(filters.TEXT & ~filters.COMMAND, is_authorized_handle)],
            FIRST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, first_name_handle)],
            LAST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, last_name_handle)],
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, registration_username_handle)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email_handle)],
            PASSWORD1: [MessageHandler(filters.TEXT & ~filters.COMMAND, password1_handle)],
            PASSWORD2: [MessageHandler(filters.TEXT & ~filters.COMMAND, password2_handle)],

        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    return conv_handler_main
