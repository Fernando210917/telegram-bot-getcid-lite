
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
    bloques = {
        'A': 602616,
        'B': 458025,
        'C': 645012,
        'D': 651419,
        'E': 582407,
        'F': 534896,
        'G': 262385,
        'H': 976021
    }
    lista = [f"{k}: {v}" for k, v in bloques.items()]
    body = "\n".join(lista)
    return (
        "✅ *Verificación exitosa:*\n\n"
        "🔐 Aquí está su *ID de Confirmación* generado:\n\n"
        f"{body}\n\n"
        "⚠️ *Importante:* guarde este código cuidadosamente para completar la activación."
    )

def preprocess_image_for_ocr(pil_image):
    image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    scaled = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    blurred = cv2.medianBlur(scaled, 3)
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 11, 2
    )
    processed = cv2.bitwise_not(thresh)
    return processed

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = update.effective_user.first_name or "usuario"
    mensaje = (
        f"👋 *Hola {nombre}*, bienvenido.\n\n"
        "📷 Puedes enviarme una imagen clara del ID de instalación para procesarla automáticamente.\n"
        "🖊️ O si prefieres, puedes escribir el ID manualmente.\n\n"
        "🔎 Estoy listo para ayudarte a obtener tu código de confirmación.\n"
        "¡Vamos allá! 🚀"
    )
    await update.message.reply_text(mensaje, parse_mode="Markdown")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    id_instalacion = update.message.text.strip()
    await update.message.reply_text("🔍 Procesando el ID ingresado...")
    respuesta = consultar_api_simulada(id_instalacion)
    await update.message.reply_text(respuesta, parse_mode="Markdown")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🖼️ Analizando imagen, extrayendo ID de instalación...")

    photo = await update.message.photo[-1].get_file()
    photo_bytes = await photo.download_as_bytearray()
    image = Image.open(BytesIO(photo_bytes)).convert("RGB")

    processed = preprocess_image_for_ocr(image)
    text = pytesseract.image_to_string(processed)
    bloques = re.findall(r'\d{6,}', text)

    if bloques and len(bloques) >= 3:
        id_instalacion = ''.join(bloques)
        await update.message.reply_text("🔎 Verificando ID...")
        respuesta = consultar_api_simulada(id_instalacion)
    else:
        respuesta = "❌ No se pudo detectar un ID de instalación en la imagen.\n\nIntenta enviarla más clara o escríbela manualmente."
    await update.message.reply_text(respuesta, parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()

if __name__ == '__main__':
    main()
