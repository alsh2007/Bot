import os
import yt_dlp
import tempfile
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler

TOKEN = os.getenv("TOKEN")
APP_URL = os.getenv("APP_URL")  # الرابط الرسمي للبوت على Railway
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

# ----------------- دوال تنزيل الفيديو -----------------
def download_audio(url):
    temp_dir = tempfile.mkdtemp()
    out_file = os.path.join(temp_dir, "%(title)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_file,
        "quiet": True,
    }

    files = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if "entries" in info:
            for entry in info["entries"]:
                filename = ydl.prepare_filename(entry)
                base, ext = os.path.splitext(filename)
                files.append(base + ".webm")
        else:
            filename = ydl.prepare_filename(info)
            base, ext = os.path.splitext(filename)
            files.append(base + ".webm")
    return files

def get_video_formats(url):
    with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = info.get("formats", [])
        result = []
        for f in formats:
            if f.get("filesize") is not None:
                size_mb = round(f["filesize"]/1024/1024, 2)
            else:
                size_mb = 0
            result.append({
                "format_id": f["format_id"],
                "resolution": f.get("format_note") or f.get("resolution") or "Unknown",
                "ext": f["ext"],
                "size": size_mb
            })
        return result

# ----------------- Handlers -----------------
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Welcome! Send me a YouTube, Instagram, or TikTok link.")

async def handle_message(update: Update, context: CallbackContext):
    url = update.message.text
    if "youtube.com" in url or "youtu.be" in url:
        formats = get_video_formats(url)
        keyboard = []
        for f in formats[:10]:  # نعرض أول 10 صيغ
            button_text = f"{f['resolution']} ({f['ext']}) {f['size']}MB"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"url|{f['format_id']}|{url}")])
        # زر تحميل صوت
        keyboard.append([InlineKeyboardButton("🔊 Download Audio", callback_data=f"audio|{url}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Select the format:", reply_markup=reply_markup)
    elif "instagram.com" in url or "tiktok.com" in url:
        await update.message.reply_text("⏳ Downloading, please wait...")
        try:
            files = download_audio(url)
            for f in files:
                with open(f, "rb") as video:
                    await update.message.reply_video(video, caption="✅ Download completed by Xas")
        except Exception as e:
            await update.message.reply_text(f"⚠️ Error: {e}")
    else:
        await update.message.reply_text("❌ Please send a valid YouTube, Instagram, or TikTok link.")

async def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data.split("|")
    if data[0] == "url":
        format_id, url = data[1], data[2]
        await query.edit_message_text("⏳ Downloading selected video...")
        ydl_opts = {"format": format_id}
        files = download_audio(url)
        for f in files:
            with open(f, "rb") as video:
                await query.message.reply_video(video, caption="✅ Download completed by Xas")
    elif data[0] == "audio":
        url = data[1]
        await query.edit_message_text("⏳ Downloading audio...")
        files = download_audio(url)
        for f in files:
            with open(f, "rb") as audio:
                await query.message.reply_audio(audio, caption="✅ Download completed by Xas")

# ----------------- Main -----------------
def main():
    app_bot = Application.builder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_bot.add_handler(CallbackQueryHandler(button_callback))

    print("🚀 Bot is running...")
    app_bot.run_polling()

if __name__ == "__main__":
    main()
