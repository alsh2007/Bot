import os
import telebot
from telebot import types
import yt_dlp
import tempfile

# جلب المتغيرات من البيئة
BOT_TOKEN = os.environ.get('BOT_TOKEN')
COOKIES = os.environ.get('COOKIES')

bot = telebot.TeleBot(BOT_TOKEN)

# دالة تحميل الفيديو/الصوت
def download_media(url, media_type, quality=None):
    ydl_opts = {
        'cookiefile': None,
        'cookiesfrombrowser': False,
        'quiet': True,
        'outtmpl': tempfile.gettempdir() + '/%(title)s.%(ext)s'
    }

    # إذا حاطين الكوكيز
    if COOKIES:
        cookies_path = os.path.join(tempfile.gettempdir(), 'cookies.txt')
        with open(cookies_path, 'w', encoding='utf-8') as f:
            f.write(COOKIES)
        ydl_opts['cookiefile'] = cookies_path

    # إعدادات الصوت
    if media_type == 'audio':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    elif media_type == 'video' and quality:
        ydl_opts['format'] = f'bestvideo[height<={quality}]+bestaudio/best'
    else:
        ydl_opts['format'] = 'best'

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if media_type == 'audio':
            filename = os.path.splitext(filename)[0] + '.mp3'
    return filename

# زر البداية
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "ارسل لي رابط اليوتيوب الي تريد تحميله:")

# استقبال الرابط
@bot.message_handler(func=lambda m: True)
def get_link(message):
    url = message.text
    markup = types.InlineKeyboardMarkup()
    btn_video = types.InlineKeyboardButton("Video", callback_data=f"video|{url}")
    btn_audio = types.InlineKeyboardButton("Audio", callback_data=f"audio|{url}")
    markup.add(btn_video, btn_audio)
    bot.send_message(message.chat.id, "اختر نوع الملف:", reply_markup=markup)

# التعامل مع الأزرار
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data
    if data.startswith("audio"):
        url = data.split("|")[1]
        bot.answer_callback_query(call.id, "جاري تحميل الصوت...")
        filename = download_media(url, 'audio')
        with open(filename, 'rb') as f:
            bot.send_audio(call.message.chat.id, f)
    elif data.startswith("video"):
        url = data.split("|")[1]
        # أزرار الجودة
        markup = types.InlineKeyboardMarkup()
        for q in [144, 240, 360, 480, 720]:
            btn = types.InlineKeyboardButton(f"{q}p", callback_data=f"video_quality|{url}|{q}")
            markup.add(btn)
        bot.send_message(call.message.chat.id, "اختر جودة الفيديو:", reply_markup=markup)
    elif data.startswith("video_quality"):
        _, url, quality = data.split("|")
        quality = int(quality)
        bot.answer_callback_query(call.id, f"جاري تحميل الفيديو {quality}p...")
        filename = download_media(url, 'video', quality)
        with open(filename, 'rb') as f:
            bot.send_video(call.message.chat.id, f)

bot.infinity_polling()
