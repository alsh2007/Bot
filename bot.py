import os
import yt_dlp
import tempfile
from flask import Flask, request
from threading import Thread
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# ----------------- المتغيرات -----------------
TOKEN = os.getenv("TOKEN")  # توكن البوت
PORT = int(os.getenv("PORT", 5000))  # بورت Railway
APP_URL = os.getenv("APP_URL")  # رابط مشروع Railway، مثال: https://mybot.up.railway.app

# ----------------- Flask -----------------
app_flask = Flask("")

@app_flask.route("/", methods=["GET"])
def home():
    return "Bot is running!"

@app_flask.route(f"/{TOKEN}", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    app_bot.update_queue.put(update)
    return "OK"

def run_flask():
    app_flask.run(host="0.0.0.0", port=PORT)

Thread(target=run_flask).start()

# ----------------- دالة تحميل الصوت -----------------
def download_audio(url):
    temp_dir = tempfile.mkdtemp()
    out_file = os.path.join(temp_dir, "%(title)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_file,
        "noplaylist": False,
        "quiet": True,
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
        else:  # فيديو واحد
            filename = ydl.prepare_filename(info)
            base, ext = os.path.splitext(filename)
            audio_file = base + ".webm"
            files.append(audio_file)

    return files

# ----------------- أوامر البوت -----------------
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Welcome! Send me a YouTube video or playlist link to get audio files.")

async def handle_message(update: Update, context: CallbackContext):
    url = update.message.text
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("❌ Please send a valid YouTube link.")
        return

    await update.message.reply_text("⏳ Downloading, please wait...")

    try:
        files = download_audio(url)
        for f in files:
            with open(f, "rb") as audio:
                await update.message.reply_audio(audio, caption="✅ Download completed by Xas")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

# ----------------- تشغيل البوت -----------------
bot = Bot(TOKEN)
app_bot = Application.builder().token(TOKEN).build()

app_bot.add_handler(CommandHandler("start", start))
app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ضبط Webhook
bot.set_webhook(f"{APP_URL}/{TOKEN}")

print("🚀 Bot is running on Railway...")
app_bot.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    webhook_path=f"/{TOKEN}",
)
