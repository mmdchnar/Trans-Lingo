import logging
import sqlite3
from uuid import uuid4
from deep_translator import GoogleTranslator
from telegram import Update, ForceReply, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, InlineQueryHandler


# connect to database
con = sqlite3.connect("users.db", check_same_thread=False)
cur = con.cursor()

# Create table if it is not exist
cur.execute('create table if not exists users (userid integer, source text, target text)')


# Define change language option
def fa(update: Update, context: CallbackContext) -> None:
    try:
        cur.execute(f'update users set target = "fa" where userid = {update.effective_user.id}')
    except sqlite3.OperationalError:
        cur.execute(f'insert into users values ({update.effective_user.id}, "auto", "fa")')
    con.commit()
    update.message.reply_text('✅ Your message will translate to فارسی🇮🇷',
                              reply_markup=ForceReply(input_field_placeholder='✅ Translate to "فارسی"'))


def en(update: Update, context: CallbackContext) -> None:
    try:
        cur.execute(f'update users set target = "en" where userid = {update.effective_user.id}')
    except sqlite3.OperationalError:
        cur.execute(f'insert into users values ({update.effective_user.id}, "auto", "en")')
    con.commit()
    update.message.reply_text('✅ Your message will translate to English🇬🇧',
                              reply_markup=ForceReply(input_field_placeholder='✅ Translate to "English"'))


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context.
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    data = cur.execute(
        "SELECT * FROM users WHERE userid = ?",
        (user.id,)).fetchone()

    if data is None:
        cur.execute(f'insert into users values ({user.id}, "auto", "fa")')
        con.commit()
        data = (user.id, 'auto', 'fa')

    update.message.reply_markdown_v2(
        fr'''Hi dear {user.mention_markdown_v2()}\.

Your message will translate to {'English🇬🇧' if data[2] == 'en' else 'فارسی🇮🇷'}\.

For change use:
/en \- Translate to English🇬🇧
/fa \- Translate to فارسی🇮🇷''',
        reply_markup=ForceReply(selective=True,
                                input_field_placeholder=f'✅ Translate to "{"English" if data[2] == "en" else "فارسی"} "...'))


def translate(update: Update, context: CallbackContext) -> None:
    """Translate the user message."""
    data = cur.execute(
        "SELECT * FROM users WHERE userid = ?",
        (update.effective_user.id,)).fetchone()
    if data is None:
        cur.execute(f'insert into users values ({update.effective_user.id}, "auto", "fa")')
        con.commit()
        data = (update.effective_user.id, 'auto', 'fa')
    translation = GoogleTranslator(source='auto', target=data[2]).translate(update.message.text)
    update.message.reply_text(translation if translation is not None else update.message.text)


def inline(update: Update, context: CallbackContext) -> None:
    """Handle the inline query."""
    query = update.inline_query.query

    if query == "":
        return

    eng = GoogleTranslator(source='auto', target='en').translate(query)
    far = GoogleTranslator(source='auto', target='fa').translate(query)

    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="English🇬🇧",
            description=eng,
            input_message_content=InputTextMessageContent(eng)),
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="فارسی🇮🇷",
            description=far,
            input_message_content=InputTextMessageContent(far))]

    update.inline_query.answer(results)


def main() -> None:
    """Start the bot."""
    # Create the Updater
    updater = Updater("TOKEN")

    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("fa", fa))
    dispatcher.add_handler(CommandHandler("en", en))

    # on non command i.e message - translate the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.all & ~Filters.command, translate))

    # on inline translation
    dispatcher.add_handler(InlineQueryHandler(inline))

    # Start the Bot
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
