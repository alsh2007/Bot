import os
import yt_dlp
import tempfile
from flask import Flask, request
from threading import Thread
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext

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

# ----------------- دوال تحميل -----------------
def get_youtube_formats(url):
    ydl_opts = {"quiet": True, "skip_download": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    formats = []
    for f in info.get("formats", []):
        if f.get("vcodec") != "none":  # فيديو فقط
            if f.get("height"):
                formats.append({"format_id": f["format_id"], "resolution": f["height"]})
    return formats

def download_media(url, format_id=None, audio_only=False):
    temp_dir = tempfile.mkdtemp()
    if audio_only:
        out_file = os.path.join(temp_dir, "%(title)s.%(ext)s")
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": out_file,
            "quiet": True,
        }
    else:
        out_file = os.path.join(temp_dir, "%(title)s.%(ext)s")
        ydl_opts = {
            "format": format_id if format_id else "best",
            "outtmpl": out_file,
            "quiet": True,
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

# ----------------- أوامر البوت -----------------
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Welcome! Send me a YouTube, Instagram, or TikTok link to download media."
    )

async def handle_message(update: Update, context: CallbackContext):
    url = update.message.text
    if "youtube.com" in url or "youtu.be" in url:
        formats = get_youtube_formats(url)
        buttons = []
        for f in formats[-5:]:  # آخر 5 دقات
            buttons.append(
                [InlineKeyboardButton(f"{f['resolution']}p", callback_data=f"yt|{url}|{f['format_id']}")]
            )
        buttons.append([InlineKeyboardButton("Audio Only", callback_data=f"yt|{url}|audio")])
        reply_markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text("Choose format:", reply_markup=reply_markup)
    elif "instagram.com" in url or "tiktok.com" in url:
        await update.message.reply_text("⏳ Downloading, please wait...")
        try:
            files = download_media(url)
            for f in files:
                with open(f, "rb") as media:
                    await update.message.reply_video(media, caption="✅ Download completed by Xas")
        except Exception as e:
            await update.message.reply_text(f"⚠️ Error: {e}")
    else:
        await update.message.reply_text("❌ Please send a valid YouTube, Instagram, or TikTok link.")

# ----------------- التعامل مع أزرار الدقة -----------------
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data.split("|")
    if data[0] == "yt":
        url = data[1]
        format_id = data[2]
        audio_only = format_id == "audio"
        await query.edit_message_text("⏳ Downloading, please wait...")
        try:
            files = download_media(url, format_id=None if audio_only else format_id, audio_only=audio_only)
            for f in files:
                with open(f, "rb") as media:
                    if audio_only:
                        await query.message.reply_audio(media, caption="✅ Download completed by Xas")
                    else:
                        await query.message.reply_video(media, caption="✅ Download completed by Xas")
        except Exception as e:
            await query.message.reply_text(f"⚠️ Error: {e}")

# ----------------- تشغيل البوت -----------------
bot = Bot(TOKEN)
app_bot = Application.builder().token(TOKEN).build()

app_bot.add_handler(CommandHandler("start", start))
app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app_bot.add_handler(CallbackQueryHandler(button_handler))

# ضبط Webhook
bot.set_webhook(f"{APP_URL}/{TOKEN}")

print("🚀 Bot is running on Railway...")
app_bot.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    webhook_path=f"/{TOKEN}",
        )
