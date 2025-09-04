import os
import yt_dlp
import tempfile
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext

BOT_TOKEN = os.getenv("BOT_TOKEN")
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

# دالة تنزيل الفيديو أو الصوت
def download_media(url, mode="audio"):
    temp_dir = tempfile.mkdtemp()
    out_file = os.path.join(temp_dir, "%(title)s.%(ext)s")

    ydl_opts = {  
        "outtmpl": out_file,
        "quiet": True,
        "nocheckcertificate": True,
        "geo_bypass": True,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    # تحديد الصيغة حسب الاختيار
    if mode == "audio":
        ydl_opts["format"] = "bestaudio/best"
    else:  # video
        ydl_opts["format"] = "bestvideo+bestaudio/best"
    
    files = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if "entries" in info:
            for entry in info["entries"]:
                filename = ydl.prepare_filename(entry)
                base, ext = os.path.splitext(filename)
                files.append(base + (".mp3" if mode=="audio" else ".mp4"))
        else:
            filename = ydl.prepare_filename(info)
            base, ext = os.path.splitext(filename)
            files.append(base + (".mp3" if mode=="audio" else ".mp4"))
    return files

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Welcome! Send me a YouTube, Instagram, or TikTok link to download audio or video.")

# معالجة الزر
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    url = query.data.split("|")[1]
    mode = query.data.split("|")[0]

    await query.message.edit_text(f"⏳ Downloading {mode}, please wait...")

    try:
        files = download_media(url, mode)
        for f in files:
            with open(f, "rb") as media:
                if mode == "audio":
                    await query.message.reply_audio(media, caption=f"✅ {mode.capitalize()} download completed!")
                else:
                    await query.message.reply_video(media, caption=f"✅ {mode.capitalize()} download completed!")
    except Exception as e:
        await query.message.reply_text(f"⚠️ Error: {e}")

async def handle_message(update: Update, context: CallbackContext):
    url = update.message.text
    # إذا الرسالة مو رابط معروف، ما يسوي شي
    if not any(x in url for x in ["youtube.com", "youtu.be", "instagram.com", "tiktok.com"]):
        return

    # زرّين للاختيار بين audio و video
    keyboard = [
        [InlineKeyboardButton("Audio 🎵", callback_data=f"audio|{url}"),
         InlineKeyboardButton("Video 🎬", callback_data=f"video|{url}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose format:", reply_markup=reply_markup)

def main():
    app_bot = Application.builder().token(BOT_TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_bot.add_handler(CallbackQueryHandler(button_handler))

    print("🚀 Bot is running...")
    app_bot.run_polling()

if __name__ == "__main__":
    main()
