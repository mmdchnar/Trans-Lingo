import logging
import sqlite3
from uuid import uuid4
from deep_translator import GoogleTranslator
from telegram import Update, ForceReply, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, InlineQueryHandler


TOKEN = 'TOKEN'

# connect to database
con = sqlite3.connect("users.db", check_same_thread=False)
cur = con.cursor()

# Create table if it is not exist
cur.execute('create table if not exists users (userid integer, source text, target text)')


# Define change language option
async def fa(update: Update, context: CallbackContext) -> None:
    try:
        cur.execute(f'update users set target = "fa" where userid = {update.effective_user.id}')
    except sqlite3.OperationalError:
        cur.execute(f'insert into users values ({update.effective_user.id}, "auto", "fa")')
    con.commit()
    await update.message.reply_text('✅ Your message will translate to فارسی🇮🇷',
                              reply_markup=ForceReply(input_field_placeholder='✅ Translate to "فارسی"'))


async def en(update: Update, context: CallbackContext) -> None:
    try:
        cur.execute(f'update users set target = "en" where userid = {update.effective_user.id}')
    except sqlite3.OperationalError:
        cur.execute(f'insert into users values ({update.effective_user.id}, "auto", "en")')
    con.commit()
    await update.message.reply_text('✅ Your message will translate to English🇬🇧',
                              reply_markup=ForceReply(input_field_placeholder='✅ Translate to "English"'))


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: CallbackContext) -> None:
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


async def translate(update: Update, context: CallbackContext) -> None:
    """Translate the user message."""
    data = cur.execute(
        "SELECT * FROM users WHERE userid = ?",
        (update.effective_user.id,)).fetchone()
    if data is None:
        cur.execute(f'insert into users values ({update.effective_user.id}, "auto", "fa")')
        con.commit()
        data = (update.effective_user.id, 'auto', 'fa')
    translation = GoogleTranslator(source='auto', target=data[2]).translate(update.message.text)
    await update.message.reply_text(translation if translation is not None else update.message.text)


async def inline(update: Update, context: CallbackContext) -> None:
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
    
    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("en", en))
    application.add_handler(CommandHandler("fa", fa))

    # on non command i.e message - translate the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate))


    # on inline translation
    application.add_handler(InlineQueryHandler(inline))

    # Start the Bot
    application.run_polling()


if __name__ == '__main__':
    main()
