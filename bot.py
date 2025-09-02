import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from yt_dlp import YoutubeDL

BOT_TOKEN = os.getenv("BOT_TOKEN")
COOKIES = os.getenv("COOKIES")  # كل الكوكيز اللي رتبتها هنا

app = Client("yt_bot", bot_token=BOT_TOKEN)

# صيغة التحميل
FORMATS = ["video", "audio"]

# يجيب جودات الفيديو المتاحة
def get_video_formats(url):
    ydl_opts = {
        "cookiefile": None,
        "cookies": COOKIES,
        "quiet": True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = info.get("formats", [])
        video_quals = []
        for f in formats:
            if f.get("vcodec") != "none" and f.get("acodec") != "none":
                # فقط جودات متوفرة
                if f["format_note"] not in video_quals:
                    video_quals.append(f["format_note"])
        return sorted(video_quals, key=lambda x: int(x.replace("p","")))

# تحميل الفيديو أو الصوت حسب الجودة
def download_media(url, ftype, quality=None):
    ydl_opts = {
        "cookiefile": None,
        "cookies": COOKIES,
        "outtmpl": "%(title)s.%(ext)s",
    }
    if ftype == "audio":
        ydl_opts["format"] = "bestaudio/best"
    elif ftype == "video" and quality:
        ydl_opts["format"] = f"bestvideo[height={quality.replace('p','')}]+bestaudio/best"
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
    return info["title"] + "." + info["ext"]

# استقبال الرابط
@app.on_message(filters.command("download"))
async def download_command(client, message):
    try:
        url = message.text.split(" ",1)[1]
    except IndexError:
        await message.reply_text("ادخل رابط بعد الامر /download")
        return
    
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(f, callback_data=f"{url}|{f}")] for f in FORMATS]
    )
    await message.reply_text("اختر الصيغة:", reply_markup=keyboard)

# التعامل مع الضغط على الأزرار
@app.on_callback_query()
async def button(client, callback_query):
    data = callback_query.data
    if "|" in data:
        url, ftype = data.split("|")
        if ftype == "video":
            # نجيب جودات الفيديو
            quals = get_video_formats(url)
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton(q, callback_data=f"{url}|video|{q}")] for q in quals]
            )
            await callback_query.message.edit_text("اختر الجودة:", reply_markup=keyboard)
        elif ftype == "audio":
            await callback_query.message.edit_text("جاري تحميل الصوت...")
            filename = download_media(url, "audio")
            await callback_query.message.reply_document(filename)
            await callback_query.message.edit_text("تم التحميل!")
    elif data.count("|")==2:
        url, ftype, quality = data.split("|")
        await callback_query.message.edit_text(f"جاري تحميل الفيديو بجودة {quality}...")
        filename = download_media(url, "video", quality)
        await callback_query.message.reply_document(filename)
        await callback_query.message.edit_text("تم التحميل!")

app.run()
