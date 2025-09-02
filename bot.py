import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from yt_dlp import YoutubeDL
from datetime import timedelta

# ===== متغيرات البوت =====
TOKEN = os.environ.get("BOT_TOKEN")  # حط الـ Bot Token مالك بالRailway
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ===== إعدادات yt-dlp =====
ydl_opts_video = {
    'format': 'bestvideo+bestaudio/best',
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'noplaylist': True,
    'quiet': True
}

ydl_opts_audio = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'noplaylist': True,
    'quiet': True
}

# ===== أزرار الدقة =====
QUALITY_BUTTONS = [
    InlineKeyboardButton("144p", callback_data="144"),
    InlineKeyboardButton("240p", callback_data="240"),
    InlineKeyboardButton("360p", callback_data="360"),
    InlineKeyboardButton("480p", callback_data="480"),
    InlineKeyboardButton("720p", callback_data="720"),
    InlineKeyboardButton("1080p", callback_data="1080"),
    InlineKeyboardButton("🎵 Audio", callback_data="audio")
]

markup = InlineKeyboardMarkup(row_width=3)
markup.add(*QUALITY_BUTTONS)

# ===== أوامر البوت =====
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply("هلا بيك! 🚀\nدز رابط YouTube، TikTok أو Instagram لتنزيله.")

@dp.message_handler()
async def download_link(message: types.Message):
    url = message.text.strip()
    try:
        await message.reply("جارٍ تجهيز روابط التحميل... ⏳", reply=False)
        # استخراج معلومات الفيديو
        with YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'video')
            duration = str(timedelta(seconds=info.get('duration', 0)))
            thumbnail = info.get('thumbnail', None)

        # حفظ بيانات المستخدم بالفيديو
        await message.reply_photo(photo=thumbnail,
                                  caption=f"اختر الدقة لتحميل: {title}\nمدة الفيديو: {duration}",
                                  reply_markup=markup)

        # حفظ المعلومات مؤقتًا بالذاكرة
        dp.current_state(user=message.from_user.id).update_data(url=url, title=title)

    except Exception as e:
        await message.reply(f"حدث خطأ أثناء معالجة الرابط: {str(e)}")

# ===== التعامل مع أزرار الدقة =====
@dp.callback_query_handler()
async def callback_download(call: types.CallbackQuery):
    await call.answer("جارٍ التحميل... ⏳")
    data = await dp.current_state(user=call.from_user.id).get_data()
    url = data.get('url')
    title = data.get('title', 'video')

    choice = call.data
    os.makedirs("downloads", exist_ok=True)

    try:
        if choice == "audio":
            opts = ydl_opts_audio
        else:
            opts = ydl_opts_video
            opts['format'] = f"bestvideo[height<={choice}]+bestaudio/best"

        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # إرسال الملف
        if choice == "audio":
            await bot.send_audio(call.from_user.id, open(filename, 'rb'),
                                 caption=f"Download completed by XAS .. مدة الفيديو: {str(timedelta(seconds=info.get('duration',0)))}")
        else:
            await bot.send_video(call.from_user.id, open(filename, 'rb'),
                                 caption=f"Download completed by XAS .. مدة الفيديو: {str(timedelta(seconds=info.get('duration',0)))}")

        os.remove(filename)  # حذف الملف بعد الإرسال
    except Exception as e:
        await bot.send_message(call.from_user.id, f"حدث خطأ أثناء التحميل: {str(e)}")

# ===== تشغيل البوت Polling =====
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
