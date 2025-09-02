import os
import yt_dlp
import tempfile
import requests
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext

TOKEN = os.getenv("TOKEN")
PORT = int(os.getenv("PORT", 5000))  # البورت للـ Replit أو Railway

# ----------------- Flask لحفظ البوت شغال -----------------
app_flask = Flask("")

@app_flask.route("/")
def home():
    return "Bot is running!"

def run_flask():
    app_flask.run(host="0.0.0.0", port=PORT)

Thread(target=run_flask).start()
# ----------------------------------------------------------

# دالة تحميل الفيديو أو الصوت من يوتيوب
def get_video_info(url):
    ydl_opts = {"quiet": True, "noplaylist": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return info

def download_file(url, path):
    ydl_opts = {"outtmpl": path, "quiet": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Welcome! Send me a YouTube, TikTok, or Instagram link to download video or audio."
    )

# ----------------- التعامل مع الرسائل -----------------
async def handle_message(update: Update, context: CallbackContext):
    url = update.message.text
    if not any(domain in url for domain in ["youtube.com", "youtu.be", "tiktok.com", "instagram.com"]):
        await update.message.reply_text("❌ Please send a valid YouTube, TikTok, or Instagram link.")
        return

    await update.message.reply_text("⏳ Processing your link...")

    try:
        info = get_video_info(url)
        title = info.get("title", "Video")
        thumbnail_url = info.get("thumbnail")

        # أزرار الدقة + تحويل لصوت
        buttons = []
        if "formats" in info:
            for f in info["formats"]:
                if f.get("acodec") != "none" or f.get("vcodec") != "none":
                    # ناخذ الدقات الشائعة فقط
                    if f.get("height") in [144, 240, 360, 480, 720, 1080]:
                        buttons.append([InlineKeyboardButton(f"{f['height']}p", callback_data=f"video|{f['format_id']}|{url}")])
        # زر الصوت
        buttons.append([InlineKeyboardButton("🎵 Audio", callback_data=f"audio|{url}")])
        keyboard = InlineKeyboardMarkup(buttons)

        if thumbnail_url:
            await update.message.reply_photo(photo=thumbnail_url, caption="Select quality or audio:", reply_markup=keyboard)
        else:
            await update.message.reply_text("Select quality or audio:", reply_markup=keyboard)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

# ----------------- التعامل مع اختيار المستخدم -----------------
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    data = query.data.split("|")
    action = data[0]

    temp_dir = tempfile.mkdtemp()

    if action == "video":
        format_id, url = data[1], data[2]
        path = os.path.join(temp_dir, "%(title)s.%(ext)s")
        ydl_opts = {"format": format_id, "outtmpl": path, "quiet": True}
        await query.edit_message_text("⏳ Downloading video...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
        # تحقق من حجم الملف، لو أكبر من 50 ميغا أرسل رابط بدلاً من الملف
        file_size = os.path.getsize(file_path)
        if file_size > 50 * 1024 * 1024:
            await query.edit_message_text(f"File too big! Download link: {url}")
        else:
            with open(file_path, "rb") as f:
                await query.edit_message_text("✅ Sending video...")
                await query.message.reply_video(f)

    elif action == "audio":
        url = data[1]
        path = os.path.join(temp_dir, "%(title)s.%(ext)s")
        ydl_opts = {"format": "bestaudio/best", "outtmpl": path, "quiet": True}
        await query.edit_message_text("⏳ Downloading audio...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            base, ext = os.path.splitext(file_path)
            file_path = base + ".webm"
        with open(file_path, "rb") as f:
            await query.edit_message_text("✅ Sending audio...")
            await query.message.reply_audio(f, caption="Downloaded by Xas")

# ----------------- تشغيل البوت -----------------
def main():
    app_bot = Application.builder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_bot.add_handler(CallbackQueryHandler(button_handler))

    print("🚀 Bot is running...")
    app_bot.run_polling()

if __name__ == "__main__":
    main()
