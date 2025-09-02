import os
import yt_dlp
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ChatAction
import math

BOT_TOKEN = os.getenv("BOT_TOKEN")

def start(update, context):
    update.message.reply_text("هلا بيك! دزلي رابط يوتيوب وأنزلك الصوت فقط 🎵")

def download_audio(update, context):
    url = update.message.text.strip()
    chat_id = update.message.chat_id

    # يبين للمستخدم أنه دايشتغل
    context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_AUDIO)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "%(id)s.%(ext)s",
        "noplaylist": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_name = f"{info['id']}.{info['ext']}"

            duration = info.get("duration", 0)
            duration_str = time_format(duration)

            caption = f"download completed by XAS ({duration_str})"

            with open(file_name, "rb") as audio:
                context.bot.send_audio(
                    chat_id=chat_id,
                    audio=audio,
                    title=info.get("title", "Audio"),
                    performer=info.get("uploader", "Unknown"),
                    caption=caption,
                )

            os.remove(file_name)

    except Exception as e:
        update.message.reply_text(f"⚠️ Error: {str(e)}")

def time_format(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h:02}:{m:02}:{s:02}"
    else:
        return f"{m:02}:{s:02}"

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, download_audio))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
