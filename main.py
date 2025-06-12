
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import boto3
import requests
import re
import os
from datetime import datetime

BOT_TOKEN = "TU_BOT_TOKEN"
GETCID_ENDPOINT = "https://getcid.info/api"  # Simulado
AWS_REGION = "us-east-1"
ADMIN_CHAT_ID = "TU_CHAT_ID_ADMIN"

textract = boto3.client("textract", region_name=AWS_REGION)

def extract_id(text):
    match = re.search(r"(\d{7}[\s-]?){9}", text.replace("\n", " "))
    if match:
        id_str = match.group().replace("-", "").replace(" ", "")
        return '-'.join([id_str[i:i+7] for i in range(0, len(id_str), 7)])
    return None

def get_lang_text(lang_code, key, name=""):
    messages = {
        "welcome": {
            "es": f"👋 ¡Bienvenido {name}!

Puedo extraer el ID de instalación desde una imagen legible o puedes digitarlo manualmente.

¡Empecemos! 😃",
            "en": f"👋 Welcome {name}!

I can extract your installation ID from a clear image or you can type it manually.

Let's get started! 😃"
        },
        "processing_image": {
            "es": "📸 Procesando imagen...",
            "en": "📸 Processing image..."
        },
        "id_detected": {
            "es": "🆔 ID de instalación detectado:",
            "en": "🆔 Installation ID detected:"
        },
        "verifying": {
            "es": "🔍 Verificando ID...",
            "en": "🔍 Verifying ID..."
        },
        "error_invalid_id": {
            "es": "❌ El ID ingresado no tiene el formato correcto (9 bloques de 7 dígitos).",
            "en": "❌ The entered ID format is incorrect (9 blocks of 7 digits)."
        },
        "error_no_id": {
            "es": "❌ No se pudo extraer un ID válido. Asegúrate de que sea legible.",
            "en": "❌ Could not extract a valid ID. Please ensure the image is clear."
        },
        "error_api": {
            "es": "❌ Error al obtener el ID de confirmación.",
            "en": "❌ Error retrieving confirmation ID."
        }
    }
    return messages[key].get(lang_code, messages[key]["en"])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.effective_user.language_code or "en"
    name = update.effective_user.first_name
    await update.message.reply_text(get_lang_text(lang, "welcome", name))

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.effective_user.language_code or "en"
    msg = await update.message.reply_text(get_lang_text(lang, "processing_image"))
    file = await update.message.photo[-1].get_file()
    img_bytes = await file.download_as_bytearray()

    ocr = textract.detect_document_text(Document={'Bytes': img_bytes})
    full_text = " ".join([b["Text"] for b in ocr["Blocks"] if b["BlockType"] == "LINE"])
    inst_id = extract_id(full_text)

    if not inst_id:
        return await msg.edit_text(get_lang_text(lang, "error_no_id"))

    await msg.edit_text(f"{get_lang_text(lang, 'id_detected')}\n{inst_id}")
    await msg.edit_text(get_lang_text(lang, "verifying"))

    try:
        response = requests.get(GETCID_ENDPOINT, params={"installation_id": inst_id})
        data = response.json()
        cid = data.get("cid", {})
    except:
        return await msg.edit_text(get_lang_text(lang, "error_api"))

    result = f"🆔 {get_lang_text(lang, 'id_detected')}\n{inst_id}\n\n🔐 ID de Confirmación:\n\n"
    result += "\n".join([f"{k}: {v}" for k, v in cid.items()])
    await msg.edit_text(result)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.effective_user.language_code or "en"
    msg = await update.message.reply_text("🕓...")
    text = update.message.text
    inst_id = extract_id(text)

    if not inst_id:
        return await msg.edit_text(get_lang_text(lang, "error_invalid_id"))

    await msg.edit_text(f"{get_lang_text(lang, 'id_detected')}\n{inst_id}")
    await msg.edit_text(get_lang_text(lang, "verifying"))

    try:
        response = requests.get(GETCID_ENDPOINT, params={"installation_id": inst_id})
        data = response.json()
        cid = data.get("cid", {})
    except:
        return await msg.edit_text(get_lang_text(lang, "error_api"))

    result = f"🆔 {get_lang_text(lang, 'id_detected')}\n{inst_id}\n\n🔐 ID de Confirmación:\n\n"
    result += "\n".join([f"{k}: {v}" for k, v in cid.items()])
    await msg.edit_text(result)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.run_polling()
