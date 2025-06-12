
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os

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
    body = "\n\n".join(lista)
    return (
        "✅ *Verificación exitosa:*\n\n"
        "🔐 Aquí está su *ID de Confirmación* generado:\n\n"
        "```text\n"
        f"{body}\n"
        "```\n\n"
        "📋 Puedes mantener presionado o hacer clic para copiar fácilmente el bloque completo."
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = update.effective_user.first_name or "usuario"
    mensaje = (
        f"👋 *Hola {nombre}*, bienvenido.\n\n"
        "✍️ Por favor escribe el *ID de instalación* manualmente para obtener tu código de confirmación.\n\n"
        "Estoy listo para ayudarte. ¡Vamos allá! 🚀"
    )
    await update.message.reply_text(mensaje, parse_mode="Markdown")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    id_instalacion = update.message.text.strip()
    processing_message = await update.message.reply_text("🔍 Procesando el ID ingresado...")
    respuesta = consultar_api_simulada(id_instalacion)
    await processing_message.edit_text(respuesta, parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()

if __name__ == '__main__':
    main()
