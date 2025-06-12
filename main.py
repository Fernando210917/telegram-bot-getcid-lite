
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import pytesseract
from PIL import Image
from io import BytesIO
import re
import numpy as np
import os
import cv2

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def consultar_api_simulada(id_instalacion):
    if id_instalacion.isdigit() and len(id_instalacion) >= 10:
        return f"✅ CID confirmado: 123-456-7890 para ID {id_instalacion}"
    return "⚠️ ID de instalación inválido o no encontrado."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hola 👋, envíame una imagen del ID de instalación o escríbelo manualmente.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    id_instalacion = update.message.text.strip()
    respuesta = consultar_api_simulada(id_instalacion)
    await update.message.reply_text(respuesta)

def preprocess_image_pytesseract(pil_image):
    image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
    blur = cv2.medianBlur(resized, 3)
    return blur

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = await update.message.photo[-1].get_file()
    photo_bytes = await photo.download_as_bytearray()
    image = Image.open(BytesIO(photo_bytes)).convert("RGB")

    processed = preprocess_image_pytesseract(image)
    text = pytesseract.image_to_string(processed)
    bloques = re.findall(r'\d{6,}', text)

    if bloques and len(bloques) >= 3:
        id_instalacion = ''.join(bloques)
        bloques_texto = ' '.join(bloques)
        respuesta = f"🧾 ID detectado por bloques:\n{bloques_texto}\n\n{consultar_api_simulada(id_instalacion)}"
    else:
        respuesta = "❌ No se pudo detectar un ID de instalación en la imagen."

    await update.message.reply_text(respuesta)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()

if __name__ == '__main__':
    main()
