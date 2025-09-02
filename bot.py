import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import io

TOKEN = "7036178118:AAGCGkRbYdCclSaTVGzPJpUI3s_yuhSQpbc"
bot = telebot.TeleBot(TOKEN)

# الكوكيز
COOKIES = {
    "GPS": "1",
    "PREF": "tz=Asia.Baghdad",
    "__Secure-1PSIDTS": "sidts-CjUB5H03P1k7K2lKsoWC7TD3cOkaD9ihsuaizvrr8r0-qcjccqOja63wfB2PKD9CQiqUMzwzZRAA",
    "__Secure-3PSIDTS": "sidts-CjUB5H03P1k7K2lKsoWC7TD3cOkaD9ihsuaizvrr8r0-qcjccqOja63wfB2PKD9CQiqUMzwzZRAA",
    "HSID": "AQPBX-7Uez5iaO92R",
    "SSID": "AK2cViX3BGZVOKNZ_",
    "APISID": "lb7BJvfKVvHF6Wl4/AkqCNHth4tnWdx7x-",
    "SAPISID": "ZN8aS95r11T-R07H/AgKpEdYH9gZBwHWyk",
    "__Secure-1PAPISID": "ZN8aS95r11T-R07H/AgKpEdYH9gZBwHWyk",
    "__Secure-3PAPISID": "ZN8aS95r11T-R07H/AgKpEdYH9gZBwHWyk",
    "SID": "g.a0000wgogZKa2qGr9cmWKqsCrmAnzNvXqgeN_K3AvQj0rqHsIVvQR_lSD2FRYRmJR9xLCZDAxwACgYKAT0SARASFQHGX2MiLp96_u2ld5rJreg8QQ0jQxoVAUF8yKqPA5sRwfGPZL5XFyuphrAy0076",
    "__Secure-1PSID": "g.a0000wgogZKa2qGr9cmWKqsCrmAnzNvXqgeN_K3AvQj0rqHsIVvQbFWmX_uel2uOWjbj2JFxqAACgYKAYESARASFQHGX2MihwNuQn0apkLsaMiMJodj8xoVAUF8yKotj5ZKhjwz4GErZNLHbt2z0076",
    "__Secure-3PSID": "g.a0000wgogZKa2qGr9cmWKqsCrmAnzNvXqgeN_K3AvQj0rqHsIVvQdoFqTDSpixMWMTjECmprAAACgYKAeMSARASFQHGX2Mio_iAnQdFHPwoAWNaXvUPsBoVAUF8yKqhVONXc6FFBqyzUJLh2WC80076",
    "LOGIN_INFO": "AFmmF2swRQIhAOJ3TgJDWHL6Qh8xv4hjbpkQrdo-LNoQP-7ZP1BFvgtFAiBt17yR3fBmK-GhktfW4pK09Pbsnm3xb4WVdl352BYDuQ:QUQ3MjNmdy0tdGNRcVhTZlhPd1NOVktnM2o5UE9RVkRZUnFEVTFNd0s2Y1hCTS00UVFpZG1zVnI3aF9fMVhBQ29WQ1FOd0hIOFZ3NmZnU1lGWFM4SDFUbG5DY1V3cm1TbFJ3YmZmT0FpVE1HOThwNkZXTVZsdHZWX2NiZzVxUlNzVERiSFJkTUx5WWZGMjYyM3l4bWh3ZzFreXJXbVVvZkpR",
    "SIDCC": "AKEyXzXc12GObj2pmXTwe1lKVL9p4IVbVQNKKNDm8RQg_n9eeCTxy7W18i3a2KkAMq7IBa_ikQ",
    "__Secure-1PSIDCC": "AKEyXzXc12GObj2pmXTwe1lKVL9p4IVbVQNKKNDm8RQg_n9eeCTxy7W18i3a2KkAMq7IBa_ikQ",
    "__Secure-3PSIDCC": "AKEyXzXH7wSR_xQHl7RlC0PoWW7AvTtTW7x0HTuANr74HsLexWeQU0IxaHMiRukqKd7SH5o4HA"
}

# حفظ رابط مؤقت لكل مستخدم
user_links = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "هلا! أرسل لي رابط يوتيوب وراح أطلع لك الصيغ المتوفرة.")

@bot.message_handler(func=lambda message: True)
def handle_link(message):
    url = message.text
    user_links[message.chat.id] = url
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Video", callback_data="format_video"),
        InlineKeyboardButton("Audio", callback_data="format_audio")
    )
    bot.send_message(message.chat.id, "اختر الصيغة:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    url = user_links.get(chat_id)
    if not url:
        bot.send_message(chat_id, "يرجى إرسال رابط أولاً.")
        return

    if call.data == "format_audio":
        bot.send_message(chat_id, "جارٍ تجهيز الصوت ...")
        ydl_opts = {
            "format": "bestaudio/best",
            "cookies": COOKIES,
            "outtmpl": "%(title)s.%(ext)s",
            "quiet": True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_stream = io.BytesIO()
            ydl.download([url])
            bot.send_message(chat_id, f"الصوت جاهز: {info['title']}.mp3")
        return

    if call.data == "format_video":
        ydl_opts = {
            "format": "best",
            "cookies": COOKIES,
            "quiet": True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = [f['format_id'] for f in info['formats'] if f['vcodec'] != 'none']
        markup = InlineKeyboardMarkup()
        for f in formats:
            markup.add(InlineKeyboardButton(f, callback_data=f"video_{f}"))
        bot.send_message(chat_id, "اختر جودة الفيديو:", reply_markup=markup)
        return

    if call.data.startswith("video_"):
        fmt = call.data.replace("video_", "")
        bot.send_message(chat_id, f"جارٍ تنزيل الفيديو بالجودة {fmt} ...")
        ydl_opts = {
            "format": fmt,
            "cookies": COOKIES,
            "outtmpl": "%(title)s.%(ext)s",
            "quiet": True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        bot.send_message(chat_id, "تم تنزيل الفيديو بنجاح!")

bot.polling()
