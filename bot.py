import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import yt_dlp

# المتغيرات من Railway
BOT_TOKEN = os.environ.get("BOT_TOKEN")
COOKIES = os.environ.get("COOKIES")  # الكوكيز كلها بسطر واحد

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("هلا! ابعثلي رابط يوتيوب وراح ارسلك الصوت.")

async def download_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    await update.message.reply_text("جاري تحميل الصوت... 🎵")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'cookiefile': None,
        'cookies': COOKIES,
        'outtmpl': 'audio.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        await update.message.reply_audio(audio=open("audio.mp3", 'rb'))
    except Exception as e:
        await update.message.reply_text(f"صار خطأ: {e}")
    finally:
        if os.path.exists("audio.mp3"):
            os.remove("audio.mp3")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_audio))
    
    app.run_polling()
