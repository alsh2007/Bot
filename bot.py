import os
os.system("pip install requests")
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp
import requests
from io import BytesIO

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# قائمة الدقات المتاحة
RESOLUTIONS = ["144p", "240p", "360p", "480p", "720p", "1080p"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("هلو! دزلي رابط الفيديو من يوتيوب أو تيك توك أو انستغرام، وأنا أرسللك الملف.")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    keyboard = [[InlineKeyboardButton(res, callback_data=f"video|{res}|{url}") for res in RESOLUTIONS],
                [InlineKeyboardButton("Audio Only", callback_data=f"audio|best|{url}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_photo(photo="https://via.placeholder.com/320x180.png?text=Preparing+Download", caption="اختر الدقة أو صوت فقط", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    type_, res, url = data.split("|")
    
    await query.edit_message_caption(caption="⏳ جاري التحميل ...")
    
    ydl_opts = {"outtmpl": "%(title)s.%(ext)s", "format": "best"}
    
    if type_ == "video":
        # اختر الدقة إذا موجودة
        ydl_opts["format"] = f"bestvideo[height<={res.replace('p','')}]+bestaudio/best"
    elif type_ == "audio":
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get("title", "video")
            duration_sec = info.get("duration", 0)
            minutes, seconds = divmod(duration_sec, 60)
            duration = f"{minutes}:{seconds:02d}"
            thumbnail_url = info.get("thumbnail")
            
            # تحميل الملف في الذاكرة
            buffer = BytesIO()
            ydl_opts_mem = ydl_opts.copy()
            ydl_opts_mem["outtmpl"] = "-"
            ydl_opts_mem["nopart"] = True
            ydl_opts_mem["progress_hooks"] = [lambda d: None]
            # تنزيل فعلي على القرص أولاً
            ydl.download([url])
            # أخذ اسم الملف الأخير
            file_name = ydl.prepare_filename(info)
            
            # إرسال الملف
            if type_ == "audio":
                with open(file_name, "rb") as f:
                    await query.message.reply_audio(audio=f, caption=f"✅ Download completed by XAS\nDuration: {duration}")
            else:
                with open(file_name, "rb") as f:
                    await query.message.reply_video(video=f, caption=f"✅ Download completed by XAS\nDuration: {duration}", supports_streaming=True)
    except Exception as e:
        await query.message.reply_text(f"❌ فشل التحميل: {e}")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
app.add_handler(CallbackQueryHandler(button))

if __name__ == "__main__":
    app.run_polling(poll_interval=5)
