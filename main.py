import logging
import os
import re
import requests
import boto3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Traducciones básicas
def get_lang_text(lang, key):
    texts = {
        "en": {
            "send_photo": "Please send a photo or paste your installation ID (9 blocks of 7 digits).",
            "invalid_id": "❌ Invalid installation ID format.",
            "cid_result": "✅ Here is your Confirmation ID (CID):\n\n{}",
            "not_found": "❌ Could not find any installation ID.",
            "api_error": "❌ Error retrieving CID. Try again later.",
            "textract_error": "❌ Error using Textract. Please try again later.",
        },
        "es": {
            "send_photo": "Por favor, envía una foto o pega tu ID de instalación (9 bloques de 7 dígitos).",
            "invalid_id": "❌ Formato de ID de instalación inválido.",
            "cid_result": "✅ Aquí está tu CID (Código de Confirmación):\n\n{}",
            "not_found": "❌ No se encontró ningún ID de instalación.",
            "api_error": "❌ Error al obtener el CID. Intenta nuevamente más tarde.",
            "textract_error": "❌ Error al usar Textract. Inténtalo más tarde.",
        },
    }
    return texts.get(lang, texts["es"]).get(key, "")

# Idioma por defecto
def get_lang(update: Update) -> str:
    return update.effective_user.language_code if update.effective_user else "es"

# Regex para ID de instalación
def extract_id(text):
    pattern = r"\d{7}(?:[-\s]?\d{7}){8}"
    match = re.search(pattern, text)
    return match.group() if match else None

# Procesar imagen
async def process_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        file_path = "/tmp/image.jpg"
        await file.download_to_drive(file_path)

        client = boto3.client("textract",
                              aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                              aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                              region_name="us-east-1")

        with open(file_path, "rb") as document:
            img_bytes = document.read()
        response = client.detect_document_text(Document={"Bytes": img_bytes})

        full_text = " ".join([block["Text"] for block in response["Blocks"] if block["BlockType"] == "LINE"])
        installation_id = extract_id(full_text)

        if not installation_id:
            await update.message.reply_text(get_lang_text(lang, "not_found"))
            return

        await get_cid_and_respond(update, installation_id, lang)

    except Exception as e:
        print(f"Textract error: {e}")
        await update.message.reply_text(get_lang_text(lang, "textract_error"))

# Procesar texto directo
async def process_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    text = update.message.text.strip()
    installation_id = extract_id(text)

    if not installation_id:
        await update.message.reply_text(get_lang_text(lang, "invalid_id"))
        return

    await get_cid_and_respond(update, installation_id, lang)

# Consultar API GetCID
async def get_cid_and_respond(update: Update, installation_id: str, lang: str):
    try:
        response = requests.get(f"https://getcid.info/api?installation_id={installation_id}")
        data = response.json()

        if "result" not in data:
            await update.message.reply_text(get_lang_text(lang, "api_error"))
            return

        await update.message.reply_text(get_lang_text(lang, "cid_result").format(data["result"]))

    except Exception as e:
        print(f"API error: {e}")
        await update.message.reply_text(get_lang_text(lang, "api_error"))

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    await update.message.reply_text(get_lang_text(lang, "send_photo"))

# Iniciar bot
def main():
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, process_image))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), process_text))

    app.run_polling()

if __name__ == "__main__":
    main()
