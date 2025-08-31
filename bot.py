import os
import sys
import subprocess
token = "7036178118:AAGCGkRbYdCclSaTVGzPJpUI3s_yuhSQpbc"

# ===============================
# تنزيل المكتبات إذا ما منصبة
# ===============================
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import telegram
except ImportError:
    install("python-telegram-bot==20.3")

try:
    import yt_dlp
except ImportError:
    install("yt-dlp")

# استيراد بعد التنصيب
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

import logging

# ===============================
# إعداد اللغات
# ===============================
LANGUAGES = {
    "en": {
        "welcome": "👋 Welcome to the bot! Please send /language to select your preferred language.",
        "choose_language": "🌐 Choose your language:",
        "idea": "This bot allows you to send a YouTube playlist link, and it will return the songs or videos as separate audio files.",
        "send_playlist": "📩 Now send me a YouTube playlist link."
    },
    "ar": {
        "welcome": "👋 أهلاً بيك بالبـوت! أرسل /language لاختيار لغتك.",
        "choose_language": "🌐 اختَر لغتك:",
        "idea": "هذا البوت يخليك ترسل رابط Playlist من يوتيوب ويرجعلك الفيديوهات أو الأغاني كملفات صوتية منفصلة.",
        "send_playlist": "📩 هسه دزلي رابط Playlist من يوتيوب."
    },
    "fa": {
        "welcome": "👋 به ربات خوش آمدید! لطفاً /language را بفرستید تا زبان خود را انتخاب کنید.",
        "choose_language": "🌐 زبان خود را انتخاب کنید:",
        "idea": "این ربات به شما اجازه می‌دهد لینک یک پلی‌لیست یوتیوب را ارسال کنید و آهنگ‌ها یا ویدیوها را به صورت فایل صوتی جداگانه دریافت کنید.",
        "send_playlist": "📩 حالا لینک پلی‌لیست یوتیوب را بفرستید."
    },
    "ru": {
        "welcome": "👋 Добро пожаловать в бота! Отправьте /language, чтобы выбрать язык.",
        "choose_language": "🌐 Выберите ваш язык:",
        "idea": "Этот бот позволяет отправить ссылку на YouTube плейлист, и он вернёт песни или видео как отдельные аудиофайлы.",
        "send_playlist": "📩 Теперь отправьте ссылку на YouTube плейлист."
    }
}

# خزن اللغة الافتراضية لكل يوزر
user_languages = {}

# ===============================
# Handlers
# ===============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_languages[update.effective_user.id] = "en"  # الافتراضي انكليزي
    await update.message.reply_text(LANGUAGES["en"]["welcome"])

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data="en")],
        [InlineKeyboardButton("🇸🇦 العربية", callback_data="ar")],
        [InlineKeyboardButton("🇮🇷 فارسی", callback_data="fa")],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="ru")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    lang = user_languages.get(update.effective_user.id, "en")
    await update.message.reply_text(LANGUAGES[lang]["choose_language"], reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_languages[query.from_user.id] = query.data
    lang = LANGUAGES[query.data]
    await query.edit_message_text(lang["idea"])
    await query.message.reply_text(lang["send_playlist"])

async def handle_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_languages.get(update.effective_user.id, "en")
    url = update.message.text

    await update.message.reply_text("⏳ Downloading playlist, please wait...")

    # إعداد yt-dlp
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "noplaylist": False,
        "quiet": True,
    }

    os.makedirs("downloads", exist_ok=True)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)

            if "entries" in info_dict:
                for entry in info_dict["entries"]:
                    file_path = ydl.prepare_filename(entry)
                    audio_file = file_path.replace(".webm", ".m4a")
                    if os.path.exists(audio_file):
                        await update.message.reply_audio(audio=open(audio_file, "rb"), title=entry.get("title"))
                        os.remove(audio_file)
            else:
                file_path = ydl.prepare_filename(info_dict)
                audio_file = file_path.replace(".webm", ".m4a")
                if os.path.exists(audio_file):
                    await update.message.reply_audio(audio=open(audio_file, "rb"), title=info_dict.get("title"))
                    os.remove(audio_file)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {str(e)}")

# ===============================
# Main
# ===============================
def main():
    TOKEN = os.getenv("TOKEN")  # من الـ Config Vars بـ Heroku
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("language", set_language))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_playlist))

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()