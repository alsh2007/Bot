import os
import yt_dlp
import tempfile
import asyncio
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
    app_flask.run(host="0.0.0.0", port=PORT, threaded=True)

Thread(target=run_flask).start()
# ----------------------------------------------------------

# دالة تنزيل الصوت (webm)
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
        if "entries" in info:  
            for entry in info["entries"]:  
                filename = ydl.prepare_filename(entry)  
                base, ext = os.path.splitext(filename)  
                audio_file = base + ".webm"  
                files.append(audio_file)  
        else:  
            filename = ydl.prepare_filename(info)  
            base, ext = os.path.splitext(filename)  
            audio_file = base + ".webm"  
            files.append(audio_file)  

    return files

# دالة تنزيل الفيديو بدون دمج (webm/mp4 حسب المصدر)
def download_video(url):
    temp_dir = tempfile.mkdtemp()
    out_file = os.path.join(temp_dir, "%(title)s.%(ext)s")

    ydl_opts = {  
        "format": "best",  # أفضل صيغة متوفرة بدون دمج
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
    await update.message.reply_text("Welcome! Send me a YouTube, Instagram, or TikTok link to get audio or video.")

# استقبال أي رابط
async def handle_message(update: Update, context: CallbackContext):
    url = update.message.text
    if not any(site in url for site in ["youtube.com", "youtu.be", "instagram.com", "tiktok.com"]):
        return

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
        await query.edit_message_text("⚠️ No URL found, please send a link again.")
        return

    choice = query.data
    await query.edit_message_text(f"⏳ Downloading {choice}... please wait.")

    try:
        if choice == "audio":
            files = await asyncio.to_thread(download_audio, url)
            for f in files:
                with open(f, "rb") as audio:
                    await query.message.reply_audio(audio, caption="✅ Audio download completed")
        elif choice == "video":
            files = await asyncio.to_thread(download_video, url)
            for f in files:
                with open(f, "rb") as video:
                    await query.message.reply_video(video, caption="✅ Video download completed")
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
