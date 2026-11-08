import os
import asyncio
import threading
from flask import Flask
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# ===== Flask - Free Web Service එක Live තියාගන්න =====
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bot is Alive! ✅"

@app_web.route('/health')
def health():
    return "OK", 200

def run_web():
    # Port 10000 - New One
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

BLOCKED = ["youtube.com", "youtu.be", "music.youtube"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! Send any Video Link.\n\n"
        "✅ TikTok / Instagram / Facebook / Twitter\n"
        "✅ Terabox / Reddit / Vimeo / Dailymotion\n"
        "✅ Any Website Video\n\n"
        "❌ YouTube / Netflix not supported"
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if any(x in url.lower() for x in BLOCKED):
        await update.message.reply_text("❌ YouTube is not supported.")
        return
    if "http" not in url:
        await update.message.reply_text("⚠️ Please send a Video Link.")
        return

    msg = await update.message.reply_text("⏳ Finding your video...")
    try:
        ydl_opts = {
            'format': 'best[ext=mp4]/best/bestvideo+bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'extractor_args': {'generic': {'impersonate': True}},
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Video')[:80]
            direct_link = info.get('url')
            if not direct_link and 'formats' in info:
                direct_link = info['formats'][-1]['url']

        if not direct_link:
            await msg.edit_text("❌ Could not get link from this site. It may be Private / DRM protected.")
            return

        await msg.edit_text(
            f"✅ **{title}**\n\n👇 Download here:\n{direct_link}\n\n⚠️ This link will expire soon, download it quickly.",
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
    except Exception as e:
        await msg.edit_text(f"❌ Error: {str(e)[:200]}\n\nTry another link.")

# ===== FIX - Event Loop Error එකට =====
async def main():
    # Flask වෙනම Thread එකක
    threading.Thread(target=run_web, daemon=True).start()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    print("Bot Started...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    # Bot එක නවත්තන්නේ නැතුව තියාගන්නවා
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
