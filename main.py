import logging
import os
import re
import requests
import boto3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

def get_lang_text(lang, key):
    texts = {
        "en": {
            "send_photo": "Please send a photo or paste your installation ID (9 blocks of 7 digits).",
            "invalid_id": "❌ Invalid installation ID format.",
            "cid_result": "✅ Here is your Confirmation ID (CID):\n\n{}",
            "not_found": "❌ Could not find any installation ID.",
            "api_error": "❌ Error retrieving CID. A test CID was generated.",
            "textract_error": "❌ Error using Textract. Please try again later.",
            "id_detected": "🔍 Detected ID:\n{}\n\n⌛ Querying CID..."
        },
        "es": {
            "send_photo": "Por favor, envía una foto o pega tu ID de instalación (9 bloques de 7 dígitos).",
            "invalid_id": "❌ Formato de ID de instalación inválido.",
            "cid_result": "✅ Aquí está tu CID (Código de Confirmación):\n\n{}",
            "not_found": "❌ No se encontró ningún ID de instalación.",
            "api_error": "❌ Error al obtener el CID. Se generó un CID de prueba.",
            "textract_error": "❌ Error al usar Textract. Inténtalo más tarde.",
            "id_detected": "🔍 ID detectado:\n{}\n\n⌛ Consultando CID..."
        },
    }
    return texts.get(lang, texts["es"]).get(key, "")

def get_lang(update: Update) -> str:
    return update.effective_user.language_code if update.effective_user else "es"

def extract_id(text):
    cleaned = re.sub(r"[\s\-_.]", "", text)
    if len(cleaned) == 63 and cleaned.isdigit():
        blocks = [cleaned[i:i+7] for i in range(0, 63, 7)]
        return " ".join(blocks)
    return None

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

        await update.message.reply_text(get_lang_text(lang, "id_detected").format(installation_id))
        await get_cid_and_respond(update, installation_id, lang)

    except Exception as e:
        print(f"Textract error: {e}")
        await update.message.reply_text(get_lang_text(lang, "textract_error"))

async def process_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    text = update.message.text.strip()
    installation_id = extract_id(text)

    if not installation_id:
        await update.message.reply_text(get_lang_text(lang, "invalid_id"))
        return

    await update.message.reply_text(get_lang_text(lang, "id_detected").format(installation_id))
    await get_cid_and_respond(update, installation_id, lang)

async def get_cid_and_respond(update: Update, installation_id: str, lang: str):
    try:
        response = requests.get(f"https://getcid.info/api?installation_id={installation_id}", timeout=5)
        data = response.json()

        if "result" not in data:
            raise ValueError("API returned invalid response")

        await update.message.reply_text(get_lang_text(lang, "cid_result").format(data["result"]))

    except Exception as e:
        print(f"API error: {e}")
        fake_cid = "716732999362407812154775536380109673582027487733658541495337958"
        await update.message.reply_text(get_lang_text(lang, "api_error"))
        await update.message.reply_text(get_lang_text(lang, "cid_result").format(fake_cid))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    await update.message.reply_text(get_lang_text(lang, "send_photo"))

def main():
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, process_image))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), process_text))

    app.run_polling()

if __name__ == "__main__":
    main()
