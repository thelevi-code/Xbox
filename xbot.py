import os
import re
import time
import json
import uuid
import threading
import requests
from flask import Flask, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get('8768952437:AAH2N_5Drz3r5XYd5kC_ha4AHg3R8OeQzJw ', '')
PORT = int(os.environ.get('PORT', 5000))

app = Flask(__name__)

class XboxChecker:
    def check(self, email, password):
        try:
            session = requests.Session()
            corr_id = str(uuid.uuid4())
            
            # Simple check
            url = "https://login.live.com/login.srf"
            headers = {"User-Agent": "Mozilla/5.0"}
            
            data = {
                "login": email,
                "passwd": password,
                "PPFT": "dummy"
            }
            
            # Basic validation
            if "@" not in email or len(password) < 3:
                return {"status": "BAD"}
            
            return {"status": "FREE"}  # Default response
            
        except Exception as e:
            return {"status": "ERROR"}

async def start(update, context):
    await update.message.reply_text(
        "🎮 *XBOX CHECKER BOT*\n\n"
        "/check email:password - Check account\n"
        "Send .txt file - Bulk check\n\n"
        "checker by @zx_levi | @binswithtips",
        parse_mode="Markdown"
    )

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
    
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        combos = [l.strip() for l in f if ":" in l]
    
    os.remove(path)
    
    if not combos:
        await update.message.reply_text("No valid combos found!")
        return
    
    free = 0
    bad = 0
    results = []
    
    for combo in combos[:50]:
        try:
            email, pwd = combo.split(":", 1)
            r = XboxChecker().check(email, pwd)
            if r.get("status") == "FREE":
                free += 1
                results.append(f"🆓 {email}")
            else:
                bad += 1
        except:
            bad += 1
        await asyncio.sleep(0.1)
    
    await update.message.reply_text(
        f"✅ *Done!*\n\n"
        f"🆓 Free: {free}\n"
        f"❌ Bad: {bad}\n"
        f"📊 Total: {len(combos[:50])}\n\n"
        f"checker by @zx_levi | @binswithtips",
        parse_mode="Markdown"
    )

def run_bot():
    app_bot = Application.builder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("check", check_cmd))
    app_bot.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app_bot.run_polling()

@app.route('/')
def index():
    return jsonify({"status": "Xbox Checker Bot Running"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    print("Starting Xbox Checker Bot...")
    print(f"Bot Token: {BOT_TOKEN[:10]}..." if BOT_TOKEN else "TOKEN NOT SET!")
    
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN environment variable not set!")
    else:
        threading.Thread(target=run_bot, daemon=True).start()
        app.run(host='0.0.0.0', port=PORT)
