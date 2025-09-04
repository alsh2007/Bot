import os
import yt_dlp
import tempfile
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 5000))

# ----------------- Flask لحفظ البوت شغال -----------------
app_flask = Flask("")

@app_flask.route("/")
def home():
    return "Bot is running!"

def run_flask():
    app_flask.run(host="0.0.0.0", port=PORT)

Thread(target=run_flask).start()
# ----------------------------------------------------------

# دالة تحويل الفيديو إلى صوت
def download_audio(url):
    temp_dir = tempfile.mkdtemp()
    out_file = os.path.join(temp_dir, "%(title)s.%(ext)s")

    ydl_opts = {  
        "format": "bestaudio/best",
        "outtmpl": out_file,
        "noplaylist": False,
        "quiet": True,
        "nocheckcertificate": True,
        "geo_bypass": True,
        "user_agent": "Mozilla/5.0",
        "cookiefile": "cookies.txt"
    }

    files = []  
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:  
        info = ydl.extract_info(url, download=True)  
        if "entries" in info:  # Playlist  
            for entry in info["entries"]:  
                filename = ydl.prepare_filename(entry)  
                base, ext = os.path.splitext(filename)  
                audio_file = base + ".webm"  
                files.append(audio_file)  
        else:  # Single video  
            filename = ydl.prepare_filename(info)  
            base, ext = os.path.splitext(filename)  
            audio_file = base + ".webm"  
            files.append(audio_file)  

    return files

# دالة تنزيل الفيديو
def download_video(url):
    temp_dir = tempfile.mkdtemp()
    out_file = os.path.join(temp_dir, "%(title)s.%(ext)s")

    ydl_opts = {  
        "format": "best",
        "outtmpl": out_file,
        "noplaylist": False,
        "quiet": True,
        "nocheckcertificate": True,
        "geo_bypass": True,
        "user_agent": "Mozilla/5.0",
        "cookiefile": "cookies.txt"
    }

    files = []  
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:  
        info = ydl.extract_info(url, download=True)  
        if "entries" in info:  
            for entry in info["entries"]:  
                filename = ydl.prepare_filename(entry)  
                files.append(filename)  
        else:  
            filename = ydl.prepare_filename(info)  
            files.append(filename)  

    return files

# استقبال أمر /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Welcome! Send me a YouTube video or playlist link to get audio or video.")

# استقبال أي رابط
async def handle_message(update: Update, context: CallbackContext):
    url = update.message.text
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("❌ Please send a valid YouTube link.")
        return

    # نحفظ الرابط بجلسة المستخدم
    context.user_data["url"] = url

    keyboard = [
        [InlineKeyboardButton("🎵 Audio", callback_data="audio"),
         InlineKeyboardButton("🎬 Video", callback_data="video")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Choose download type:", reply_markup=reply_markup)

# معالجة الضغط على الأزرار
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    url = context.user_data.get("url")
    if not url:
        await query.edit_message_text("⚠️ No URL found, please send a YouTube link again.")
        return

    choice = query.data
    await query.edit_message_text(f"⏳ Downloading {choice}... please wait.")

    try:
        if choice == "audio":
            files = download_audio(url)
            for f in files:
                with open(f, "rb") as audio:
                    await query.message.reply_audio(audio, caption="✅ Audio download completed by Xas")
        elif choice == "video":
            files = download_video(url)
            for f in files:
                with open(f, "rb") as video:
                    await query.message.reply_video(video, caption="✅ Video download completed by Xas")
    except Exception as e:
        await query.message.reply_text(f"⚠️ Error: {e}")

def main():
    app_bot = Application.builder().token(BOT_TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))  
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  
    app_bot.add_handler(CallbackQueryHandler(button_handler))

    print("🚀 Bot is running...")  
    app_bot.run_polling()

if __name__ == "__main__":
    main()
