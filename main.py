
import os
import asyncio
import threading
import glob
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! Send any Video Link.\n\n"
        "Supported: TikTok / Instagram / Facebook / Twitter\n"
        "Terabox / Reddit / Vimeo / Dailymotion\n\n"
        "Not Supported: YouTube / Netflix\n\n"
        "Send a link and I will send you the video."
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if any(x in url.lower() for x in BLOCKED):
        await update.message.reply_text("YouTube is not supported.")
        return
    if "http" not in url:
        await update.message.reply_text("Please send a Video Link.")
        return

    msg = await update.message.reply_text("Downloading video... Please wait...")

    # Clean old files
    for f in glob.glob("video_*"):
        try:
            os.remove(f)
        except:
            pass

    try:
        # Download video - Under 48MB for Telegram limit
        ydl_opts = {
            'format': 'best[ext=mp4][filesize<48M]/best[filesize<48M]/best[height<=720][ext=mp4]/best',
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

        # Find downloaded file
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

        await msg.edit_text("Uploading video...")

        # Send video directly
        with open(file_path, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                caption=f"{title}",
                parse_mode="Markdown"
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
