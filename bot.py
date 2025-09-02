import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from yt_dlp import YoutubeDL

BOT_TOKEN = os.environ.get("BOT_TOKEN")
COOKIES = os.environ.get("COOKIES")  # خليها None إذا ما عندك

# تخزين روابط مؤقتة
user_links = {}

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "هلا! ارسل رابط يوتيوب لتحميله."
    )

def handle_message(update: Update, context: CallbackContext):
    url = update.message.text
    user_id = update.message.from_user.id
    user_links[user_id] = url

    keyboard = [["🎵 صوت", "🎥 فيديو"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text("اختر ما تريد تحميله:", reply_markup=reply_markup)

def download_media(url, choice):
    ydl_opts = {
        "cookiefile": None if not COOKIES else COOKIES,
        "outtmpl": "%(title)s.%(ext)s"
    }

    if choice == "audio":
        ydl_opts["format"] = "bestaudio/best"
    else:
        ydl_opts["format"] = "bestvideo+bestaudio/best"

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

def handle_choice(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    text = update.message.text

    if user_id not in user_links:
        update.message.reply_text("أرسل الرابط أولاً.")
        return

    url = user_links[user_id]
    update.message.reply_text("جارٍ التحميل، انتظر شوي...")

    choice = "audio" if "صوت" in text else "video"
    file_path = download_media(url, choice)

    update.message.reply_document(open(file_path, "rb"))
    del user_links[user_id]

def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(MessageHandler(Filters.regex("^(🎵 صوت|🎥 فيديو)$"), handle_choice))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
