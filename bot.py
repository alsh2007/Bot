import os
import yt_dlp
import tempfile
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext

TOKEN = os.getenv("TOKEN")
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

# دالة تحميل الصوت
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

# دالة تحميل الفيديو بدقة معينة
def download_video(url, resolution):
    temp_dir = tempfile.mkdtemp()
    out_file = os.path.join(temp_dir, "%(title)s.%(ext)s")
    ydl_opts = {
        "format": f"bestvideo[height<={resolution}]+bestaudio/best",
        "outtmpl": out_file,
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename, info.get("thumbnail", None)

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Welcome! Send me a YouTube, TikTok, or Instagram link to download.")

async def handle_message(update: Update, context: CallbackContext):
    url = update.message.text
    if not any(x in url for x in ["youtube.com", "youtu.be", "tiktok.com", "instagram.com"]):
        await update.message.reply_text("❌ Please send a valid link.")
        return

    # فقط لليوتيوب نعرض أزرار الدقة
    if "youtube" in url or "youtu.be" in url:
        buttons = [
            [InlineKeyboardButton("144p", callback_data=f"{url}|144")],
            [InlineKeyboardButton("240p", callback_data=f"{url}|240")],
            [InlineKeyboardButton("360p", callback_data=f"{url}|360")],
            [InlineKeyboardButton("480p", callback_data=f"{url}|480")],
            [InlineKeyboardButton("720p", callback_data=f"{url}|720")],
            [InlineKeyboardButton("1080p", callback_data=f"{url}|1080")],
            [InlineKeyboardButton("Audio Only", callback_data=f"{url}|audio")]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text("Choose video resolution or audio:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("⏳ Downloading, please wait...")
        try:
            files = download_audio(url)
            for f in files:
                with open(f, "rb") as audio:
                    await update.message.reply_audio(audio, caption="✅ Download completed")
        except Exception as e:
            await update.message.reply_text(f"⚠️ Error: {e}")

async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data
    url, choice = data.split("|")
    await query.edit_message_text("⏳ Downloading, please wait...")

    try:
        if choice == "audio":
            files = download_audio(url)
            for f in files:
                with open(f, "rb") as audio:
                    await query.message.reply_audio(audio, caption="✅ Download completed")
        else:
            file_path, thumbnail = download_video(url, choice)
            if thumbnail:
                await query.message.reply_photo(photo=thumbnail, caption=f"✅ Download completed ({choice}p)")
            with open(file_path, "rb") as video:
                await query.message.reply_video(video, caption=f"✅ Download completed ({choice}p)")
    except Exception as e:
        await query.message.reply_text(f"⚠️ Error: {e}")

def main():
    app_bot = Application.builder().token(TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_bot.add_handler(CallbackQueryHandler(button))

    print("🚀 Bot is running...")
    app_bot.run_polling()

if __name__ == "__main__":
    main()
