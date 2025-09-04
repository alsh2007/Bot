from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import yt_dlp
import tempfile
import os
import imageio_ffmpeg as ffmpeg  # للتأكد من وجود ffmpeg داخلي

# دالة لاختيار رابط وتحليل نوعه
def get_video_info(url):
    ydl_opts = {'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return info

# دالة تنزيل الصوت
def download_audio(url):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': temp_file.name,
        'quiet': True,
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec':'mp3','preferredquality':'192'}]
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return temp_file.name

# دالة تنزيل الفيديو
def download_video(url):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': temp_file.name,
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return temp_file.name

# استقبال الرسائل
def handle_message(update: Update, context: CallbackContext):
    url = update.message.text.strip()
    # اذا الرسالة مو رابط، ما نسوي شي
    if not url.startswith(('http://','https://')):
        return
    
    # نرسل زرين: Audio و Video
    keyboard = [
        [InlineKeyboardButton("Audio", callback_data=f"audio|{url}"),
         InlineKeyboardButton("Video", callback_data=f"video|{url}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("اختر ما تريد تنزيله:", reply_markup=reply_markup)

# التعامل ويا الزر
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data = query.data.split("|")
    action, url = data[0], data[1]

    msg = query.message.reply_text("جاري التحميل... ⏳")

    try:
        if action == "audio":
            file_path = download_audio(url)
            query.message.reply_audio(audio=open(file_path, 'rb'))
        elif action == "video":
            file_path = download_video(url)
            query.message.reply_video(video=open(file_path, 'rb'))
    except Exception as e:
        query.message.reply_text(f"حدث خطأ: {e}")
    finally:
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        msg.delete()

# البداية
def start(update: Update, context: CallbackContext):
    update.message.reply_text("هلو! أرسل رابط يوتيوب/إنستا/تيك توك لتنزيله.")

if __name__ == '__main__':
    TOKEN = "YOUR_BOT_TOKEN_HERE"
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(button_handler))

    updater.start_polling()
    updater.idle()
