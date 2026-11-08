import os
import re
import asyncio
import threading
import subprocess
import yt_dlp
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIG ---
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = "@bigolive_asia"

# Flask for Render Keep Alive
app_flask = Flask(__name__)
@app_flask.route('/')
def home():
    return "YADANAR Bot is Running - 2GB Mode!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

# --- START COMMAND ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌍 ŸADAÑAR 💖 Video Downloader\n\n"
        "Send me any Video Link:\n"
        "TikTok | Instagram | Facebook | YouTube | Twitter/X | Reddit & More\n\n"
        "✅ Now Supports Up To 2GB Videos!\n"
        "✅ Send Link + mp3 for Audio\n"
        "✅ Forward Telegram Video Also Works\n\n"
        f"📣 Join: {CHANNEL}"
    )

# --- HELPER: CLEAN FILENAME ---
def clean_name(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)[:80]

# --- HANDLE LINK ---
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.message.from_user.id

    is_audio = False
    if text.lower().endswith(" mp3") or text.lower().endswith("mp3"):
        is_audio = True
        text = text[:-3].strip()

    if "http" not in text:
        await update.message.reply_text("❌ Please send a valid Video Link bro!")
        return

    msg = await update.message.reply_text("⏳ Downloading... Please wait, 2GB mode is ON 🔥")

    # 2GB - Local API Server Mode
    format_str = 'best[ext=mp4][filesize<1950M]/best[filesize<1950M]/best'
    if is_audio:
        format_str = 'bestaudio/best'

    ydl_opts = {
        'format': format_str,
        'outtmpl': f'%(title)s_{user_id}.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}] if is_audio else [],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(text, download=True)
            file_path = ydl.prepare_filename(info)
            if is_audio:
                file_path = os.path.splitext(file_path)[0] + ".mp3"
            
            title = info.get('title', 'Video')[:80]
            file_size = os.path.getsize(file_path) / (1024 * 1024)
            
            # 2GB Limit Check
            if file_size > 1950:
                await msg.edit_text("❌ File is bigger than 2GB bro! Can't send.")
                os.remove(file_path)
                return

            await msg.edit_text(f"📤 Uploading... ({file_size:.1f} MB) Please wait...")

            caption = f"✅ {title}\n\n📣 Join: {CHANNEL}"

            with open(file_path, 'rb') as f:
                if is_audio:
                    await update.message.reply_audio(audio=f, caption=caption, title=title)
                else:
                    await update.message.reply_video(video=f, caption=caption, supports_streaming=True)

            await msg.delete()
            os.remove(file_path)

    except Exception as e:
        err = str(e)
        print(f"Error: {err}")
        try:
            await msg.edit_text(f"❌ Failed! {err[:250]}")
        except:
            pass
        # Clean leftover files
        for f in os.listdir('.'):
            if str(user_id) in f and (f.endswith('.mp4') or f.endswith('.mp3') or f.endswith('.webm') or f.endswith('.mkv')):
                try: os.remove(f)
                except: pass

# --- HANDLE FORWARDED TELEGRAM VIDEO ---
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ Telegram Video Downloading... Please wait...")
    try:
        video = update.message.video or update.message.document
        file = await video.get_file()
        file_path = f"tg_video_{video.file_unique_id}.mp4"
        await file.download_to_drive(file_path)
        await msg.edit_text("📤 Uploading video...")
        with open(file_path, 'rb') as f:
            await update.message.reply_video(
                video=f,
                caption=f"✅ Telegram Video Downloaded\n\n📣 {CHANNEL}",
                supports_streaming=True
            )
        await msg.delete()
        os.remove(file_path)
    except Exception as e:
        await msg.edit_text(f"❌ Error: {str(e)[:200]}")

# --- MAIN ---
async def main():
    threading.Thread(target=run_web, daemon=True).start()
    
    # --- LOCAL BOT API SERVER - 2GB MODE ---
    # Render eke Dockerfile eken run wena telegram-bot-api server ekata connect wenawa
    app = Application.builder().token(TOKEN).base_url("http://localhost:8081/bot").base_file_url("http://localhost:8081/file/bot").local_mode(True).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video))
    
    print("Bot Started... 2GB Mode ON!")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
