import os
import logging
import boto3
import re
import tempfile
import requests
from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")

# Configure logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Initialize Textract client
textract = boto3.client(
    "textract",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# Dummy function to simulate getcid.info verification
def verificar_id(id_instalacion):
    if id_instalacion.isdigit() and len(id_instalacion) >= 10:
        return (
            "✅ Verificación exitosa:\n\n"
            "A: 602616\n\n"
            "B: 458025\n\n"
            "C: 645012\n\n"
            "D: 651419\n\n"
            "E: 582407\n\n"
            "F: 534896\n\n"
            "G: 262385\n\n"
            "H: 976021"
        )
    return "⚠️ El ID de instalación extraído no es válido."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = update.effective_user.first_name
    bienvenida = (
        f"👋 Bienvenido {nombre}, puedo extraer el ID de instalación desde una captura o foto "
        "legible y notoria.\n\n"
        "📎 También puedes digitarlo manualmente si lo prefieres.\n\n"
        "🚀 Empecemos 😃"
    )
    await update.message.reply_text(bienvenida)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    id_instalacion = update.message.text.strip()
    msg = await update.message.reply_text("⏳ Procesando el ID ingresado...")
    resultado = verificar_id(id_instalacion)
    await msg.edit_text(resultado)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("📸 Imagen recibida. Extrayendo ID de instalación...")
    photo = update.message.photo[-1]
    photo_file = await photo.get_file()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tf:
        await photo_file.download_to_drive(tf.name)
        with open(tf.name, "rb") as document:
            image_bytes = document.read()
        response = textract.detect_document_text(Document={'Bytes': image_bytes})
        text = " ".join([block["Text"] for block in response["Blocks"] if block["BlockType"] == "LINE"])
        id_match = re.search(r"(\d{7,}-?){2,}", text.replace(" ", "").replace("\n", ""))
        if id_match:
            id_instalacion = id_match.group(0).replace("-", "")
            resultado = verificar_id(id_instalacion)
        else:
            resultado = "❌ No se pudo extraer un ID de instalación válido de la imagen."
    await msg.edit_text(resultado)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()

if __name__ == "__main__":
    main()
