import os
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("هلا 🙌 دزلي رابط يوتيوب وأنزلك الصوت 🎶")

# تحميل الصوت
async def download_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    print(f"📩 استلمت: {text}")   # Debug

    if not text.startswith("http"):
        await update.message.reply_text("⚠️ دزلي رابط صحيح 🙏")
        return

    await update.message.reply_text("⏳ دا ينزل الصوت...")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "%(id)s.%(ext)s",
        "noplaylist": True,
        "quiet": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(text, download=True)
            file_name = f"{info['id']}.{info['ext']}"

            with open(file_name, "rb") as audio:
                await update.message.reply_audio(
                    audio=audio,
                    title=info.get("title", "Audio"),
                    performer=info.get("uploader", "")
                )

            os.remove(file_name)

    except Exception as e:
        print(f"❌ Error: {e}")  # Debug
        await update.message.reply_text(f"⚠️ صار خطأ: {str(e)}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    # نخلي أي رسالة نصية تمر
    app.add_handler(MessageHandler(filters.TEXT, download_audio))

    app.run_polling()

if __name__ == "__main__":
    main()
