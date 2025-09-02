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

# دالة تنزيل الفيديو/الصوت
def download_media(url, format_option):
    temp_dir = tempfile.mkdtemp()
    out_file = os.path.join(temp_dir, "%(title)s.%(ext)s")

    ydl_opts = {
        "format": format_option,
        "outtmpl": out_file,
        "quiet": True,
        "noplaylist": False,
        "nocheckcertificate": True,
        "http_headers": {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename, info.get("duration"), info.get("thumbnail")

# تحويل الثواني لوقت
def format_duration(seconds):
    mins, sec = divmod(seconds, 60)
    hour, mins = divmod(mins, 60)
    if hour:
        return f"{hour:02}:{mins:02}:{sec:02}"
    else:
        return f"{mins:02}:{sec:02}"

# START
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Welcome! Send a YouTube, TikTok or Instagram link to download media.")

# HANDLER للرسائل
async def handle_message(update: Update, context: CallbackContext):
    url = update.message.text.strip()
    if "youtube.com" not in url and "youtu.be" not in url and "tiktok.com" not in url and "instagram.com" not in url:
        await update.message.reply_text("❌ Please send a valid link.")
        return

    keyboard = [
        [InlineKeyboardButton("144p", callback_data=f"{url}|best[height<=144]"),
         InlineKeyboardButton("240p", callback_data=f"{url}|best[height<=240]")],
        [InlineKeyboardButton("360p", callback_data=f"{url}|best[height<=360]"),
         InlineKeyboardButton("480p", callback_data=f"{url}|best[height<=480]")],
        [InlineKeyboardButton("720p", callback_data=f"{url}|best[height<=720]"),
         InlineKeyboardButton("1080p", callback_data=f"{url}|best[height<=1080]")],
        [InlineKeyboardButton("Audio only 🎵", callback_data=f"{url}|bestaudio")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose the format / quality:", reply_markup=reply_markup)

# CALLBACK HANDLER للأزرار
async def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data
    url, fmt = data.split("|")

    msg = await query.message.reply_text("⏳ Downloading, please wait...")
    try:
        file_path, duration, thumbnail = download_media(url, fmt)
        caption = f"✅ Download completed by XAS\nDuration: {format_duration(duration)}"
        if fmt == "bestaudio":
            with open(file_path, "rb") as f:
                await query.message.reply_audio(f, caption=caption, thumb=thumbnail)
        else:
            with open(file_path, "rb") as f:
                await query.message.reply_video(f, caption=caption, thumb=thumbnail)
    except Exception as e:
        await query.message.reply_text(f"⚠️ Error: {e}")
    await msg.delete()

# MAIN
def main():
    app_bot = Application.builder().token(TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_bot.add_handler(CallbackQueryHandler(button_callback))

    print("🚀 Bot is running...")
    app_bot.run_polling()

if __name__ == "__main__":
    main()
