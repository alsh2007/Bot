import os
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# التوكن من Secrets
TOKEN = os.environ['TOKEN']

# رسالة البداية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! 🌟\n\n"
        "Send /language to select your language.\n"
        "Or directly send me a YouTube playlist/video link 🎶"
    )

# اختيار اللغة (بسيط للتجربة، نفس اللغات مثل قبل)
async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Choose language:\nArabic | English | فارسی | Русский"
    )

# دالة تنزيل ملف صوتي
def download_audio(url, out_path="downloads"):
    os.makedirs(out_path, exist_ok=True)
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{out_path}/%(title)s.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if "entries" in info:  # Playlist
            return [os.path.join(out_path, f"{entry['title']}.mp3") for entry in info["entries"]]
        else:  # Single video
            return [os.path.join(out_path, f"{info['title']}.mp3")]

# التعامل ويا الروابط
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("⚠️ Please send a valid YouTube video or playlist link.")
        return

    await update.message.reply_text("⏳ Downloading... please wait")

    try:
        files = download_audio(url)
        for file_path in files:
            with open(file_path, "rb") as f:
                await update.message.reply_audio(
                    audio=f,
                    caption="✅ Download completed by Xas"
                )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

# تشغيل البوت
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("language", language))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.run_polling()

if __name__ == "__main__":
    main()
