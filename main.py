import os
import logging
import requests
import boto3
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Simula el procesamiento con getcid.info (reemplazar por la API real si se tiene endpoint y token)
def consultar_api_simulada(id_instalacion):
    if id_instalacion.isdigit() and len(id_instalacion) >= 10:
        return f"✅ Verificación exitosa:\n\nA: 602616\n\nB: 458025\n\nC: 645012\n\nD: 651419\n\nE: 582407\n\nF: 534896\n\nG: 262385\n\nH: 976021"
    return "⚠️ El ID de instalación ingresado no es válido o no se encontró información."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = update.effective_user.first_name
    mensaje = f"👋 Bienvenido {nombre}, puedes ingresar el ID de instalación manualmente para verificarlo.\n\n🚀 Empecemos:"
    await update.message.reply_text(mensaje)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    id_instalacion = update.message.text.strip()
    status_msg = await update.message.reply_text("⏳ Procesando el ID ingresado...")
    respuesta = consultar_api_simulada(id_instalacion)
    await status_msg.edit_text(respuesta)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()

if __name__ == "__main__":
    main()
