import os
import yt_dlp
import tempfile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext

TOKEN = os.getenv("TOKEN")

# دالة تحميل الفيديو أو الصوت
def get_video_info(url):
    ydl_opts = {"quiet": True, "format": "bestvideo+bestaudio/best"}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return info

def download_video(url, resolution):
    temp_dir = tempfile.mkdtemp()
    out_file = os.path.join(temp_dir, "%(title)s.%(ext)s")
    ydl_opts = {
        "format": f"bestvideo[height<={resolution}]+bestaudio/best" if resolution != "audio" else "bestaudio/best",
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
                if resolution == "audio":
                    base, ext = os.path.splitext(filename)
                    audio_file = base + ".webm"
                    files.append(audio_file)
                else:
                    files.append(filename)
        else:
            filename = ydl.prepare_filename(info)
            if resolution == "audio":
                base, ext = os.path.splitext(filename)
                audio_file = base + ".webm"
                files.append(audio_file)
            else:
                files.append(filename)
    return files

# دالة /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Welcome! Send me a YouTube video link to get started.")

# دالة استقبال الروابط
async def handle_message(update: Update, context: CallbackContext):
    url = update.message.text
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("❌ Please send a valid YouTube link.")
        return

    await update.message.reply_text("⏳ Fetching video info...")
    info = get_video_info(url)
    title = info.get("title", "Video")
    thumbnail = info.get("thumbnail")

    # إعداد الأزرار للدقات
    keyboard = [
        [InlineKeyboardButton("144p", callback_data=f"{url}|144")],
        [InlineKeyboardButton("240p", callback_data=f"{url}|240")],
        [InlineKeyboardButton("360p", callback_data=f"{url}|360")],
        [InlineKeyboardButton("480p", callback_data=f"{url}|480")],
        [InlineKeyboardButton("720p", callback_data=f"{url}|720")],
        [InlineKeyboardButton("1080p", callback_data=f"{url}|1080")],
        [InlineKeyboardButton("🎵 Audio Only", callback_data=f"{url}|audio")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_photo(photo=thumbnail, caption=f"Select download option for: {title}", reply_markup=reply_markup)

# دالة الضغط على الأزرار
async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data
    url, choice = data.split("|")
    await query.edit_message_caption(caption=f"⏳ Downloading {choice}...")

    try:
        files = download_video(url, choice)
        for f in files:
            with open(f, "rb") as media:
                if choice == "audio":
                    await query.message.reply_audio(media, caption="✅ Download completed!")
                else:
                    await query.message.reply_video(media, caption="✅ Download completed!")
    except Exception as e:
        await query.message.reply_text(f"⚠️ Error: {e}")

# إعداد التطبيق
def main():
    app_bot = Application.builder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_bot.add_handler(CallbackQueryHandler(button))

    print("🚀 Bot is running...")
    app_bot.run_polling()

if __name__ == "__main__":
    main()
