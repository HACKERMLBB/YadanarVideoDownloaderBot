import os
import asyncio
import threading
import glob
import re
from flask import Flask
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# Flask - Keep Web Service Alive
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bot is Alive!"

@app_web.route('/health')
def health():
    return "OK", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

BLOCKED = ["youtube.com", "youtu.be", "music.youtube"]

WELCOME_MSG = """👋 Welcome to 🌍 ŸADAÑAR 💖 Video Downloader

⛔⛔ YOUTUBE NOT WORKING ⛔
❌ PLEASE DON'T SEND YOUTUBE LINKS ❌

✅ 1000+ WEBSITES WORKING ✅
✅ ANY WEBSITE WORKING ✅

📱 SOCIAL MEDIA:
- TikTok
- Instagram - Reels / Posts / Stories
- Facebook - Videos / Reels
- Twitter / X
- Reddit
- Pinterest
- Snapchat
- Tumblr

🎬 VIDEO SITES:
- Vimeo
- Dailymotion
- Twitch - Clips / VOD
- Streamable
- MediaFire / Terabox
- Google Drive - Public Link
- Any Direct MP4 Link

📌 Just Send Link & Get Video!
🎵 Send Link + mp3 For Audio
🚫 No Watermark For TikTok

📣 Channel: @bigolive_asia
⚡ Fast & Free 24/7"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MSG)

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    lower_text = text.lower()
    is_mp3 = "mp3" in lower_text

    urls = re.findall(r'https?://\S+', text)
    if not urls:
        await update.message.reply_text("Please send a Video Link.")
        return

    url = urls[0]

    if any(x in url.lower() for x in BLOCKED):
        await update.message.reply_text("⛔ YOUTUBE NOT WORKING ⛔\n\nPLEASE DON'T SEND YOUTUBE LINKS ❌")
        return

    for f in glob.glob("video_*") + glob.glob("audio_*"):
        try:
            os.remove(f)
        except:
            pass

    if is_mp3:
        msg = await update.message.reply_text("🎵 Downloading Audio... Please wait...")
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'audio_%(id)s.%(ext)s',
                'quiet': True,
                'no_warnings': True,
                'noplaylist': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Audio')[:100]

            files = glob.glob("audio_*")
            if not files:
                await msg.edit_text("Could not download audio.")
                return

            file_path = files[0]
            await msg.edit_text("📤 Uploading Audio...")
            with open(file_path, 'rb') as audio_file:
                await update.message.reply_audio(
                    audio=audio_file,
                    title=title,
                    caption=f"🎵 {title}"
                )
            await msg.delete()
            os.remove(file_path)
            return
        except Exception as e:
            await msg.edit_text(f"Error: {str(e)[:200]}\n\nTry another link.")
            return

    msg = await update.message.reply_text("⏳ Downloading video... Please wait...")

    try:
        if "tiktok.com" in url.lower():
            format_str = 'best[ext=mp4][filesize<48M]/best[filesize<48M]/best'
        else:
            format_str = 'best[ext=mp4][filesize<48M]/best[filesize<48M]/best[height<=720][ext=mp4]/best'

        ydl_opts = {
            'format': format_str,
            'outtmpl': 'video_%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'merge_output_format': 'mp4',
            'extractor_args': {'generic': {'impersonate': True}},
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Video')[:100]

        files = glob.glob("video_*")
        if not files:
            await msg.edit_text("Could not download video. It may be Private.")
            return

        file_path = files[0]
        file_size = os.path.getsize(file_path) / (1024 * 1024)

        if file_size > 49:
            await msg.edit_text(f"Video is too large ({file_size:.1f}MB). Telegram limit is 50MB.")
            os.remove(file_path)
            return

        await msg.edit_text("📤 Uploading video...")

        with open(file_path, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                caption=f"✅ {title}\n\n📣 @bigolive_asia"
            )

        await msg.delete()
        os.remove(file_path)

    except Exception as e:
        await msg.edit_text(f"Error: {str(e)[:200]}\n\nTry another link.")
        for f in glob.glob("video_*"):
            try:
                os.remove(f)
            except:
                pass

# Fix for Event Loop Error
async def main():
    threading.Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    print("Bot Started...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
