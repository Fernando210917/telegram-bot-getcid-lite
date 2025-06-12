
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

ADMIN_EMAIL = "fernando210917@gmail.com"

# Memoria simulada
users = {}
products = {
    "Windows 10 Pro": {"price": 100, "stock": []},
    "Office 2019": {"price": 120, "stock": []}
}
recharge_points = {}
rewards_threshold = 5

# Utilidades
def get_user_id(update: Update):
    return update.effective_user.id

def get_user_email(update: Update):
    return users.get(get_user_id(update), {}).get("email", "Desconocido")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = get_user_id(update)
    if user_id not in users:
        users[user_id] = {"email": f"user{user_id}@email.com", "balance": 0, "credits": 0, "recharge_count": 0}
    buttons = [
        [InlineKeyboardButton("🛒 Ver productos", callback_data="view_products")],
        [InlineKeyboardButton("💳 Recargar saldo", callback_data="recharge")],
        [InlineKeyboardButton("📦 Realizar pedido", callback_data="order_product")]
    ]
    if get_user_email(update) == ADMIN_EMAIL:
        buttons.append([InlineKeyboardButton("⚙️ Administrador", callback_data="admin")])
    await update.message.reply_text(f"Bienvenido {update.effective_user.first_name}, elige una opción:", reply_markup=InlineKeyboardMarkup(buttons))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = get_user_id(update)

    if query.data == "view_products":
        text = "📋 *Productos disponibles:*

"
        for name, data in products.items():
            text += f"🔹 *{name}* - {data['price']} Bs
📦 Stock: {len(data['stock'])}

"
        await query.edit_message_text(text=text, parse_mode="Markdown")

    elif query.data == "recharge":
        buttons = [
            [InlineKeyboardButton("100 Bs", callback_data="pay_100")],
            [InlineKeyboardButton("200 Bs", callback_data="pay_200")],
            [InlineKeyboardButton("300 Bs", callback_data="pay_300")],
            [InlineKeyboardButton("Ya realicé el pago", callback_data="payment_done")]
        ]
        await query.edit_message_text("Selecciona el monto a recargar y envía el comprobante de pago.

Aquí está tu QR para el pago:", reply_markup=InlineKeyboardMarkup(buttons))

    elif query.data == "order_product":
        buttons = [[InlineKeyboardButton(name, callback_data=f"order_{name}")] for name in products]
        await query.edit_message_text("Selecciona el producto:", reply_markup=InlineKeyboardMarkup(buttons))

    elif query.data.startswith("order_"):
        product_name = query.data.replace("order_", "")
        product = products.get(product_name)
        if product and product["stock"]:
            price = product["price"]
            if users[user_id]["balance"] >= price:
                license = product["stock"].pop(0)
                users[user_id]["balance"] -= price
                users[user_id]["credits"] += 1
                await query.edit_message_text(
                    f"✅ *Licencia entregada:*

🔹 Producto: {product_name}
🔑 Licencia: `{license}`
💰 Saldo restante: {users[user_id]['balance']} Bs
🎫 Créditos GetCID: {users[user_id]['credits']}

👉 Usa el bot: @getcid_bot",
                    parse_mode="Markdown")
            else:
                await query.edit_message_text("❌ No tienes saldo suficiente.")
        else:
            await query.edit_message_text("❌ Stock no disponible para este producto.")

    elif query.data.startswith("pay_"):
        amount = int(query.data.split("_")[1])
        users[user_id]["balance"] += amount
        users[user_id]["recharge_count"] += 1
        recharge_points[user_id] = recharge_points.get(user_id, 0) + (amount // 100)
        previous = users[user_id]["balance"] - amount
        text = f"✅ Recarga exitosa

Saldo anterior: {previous} Bs
Saldo actual: {users[user_id]['balance']} Bs"
        if recharge_points[user_id] >= rewards_threshold:
            recharge_points[user_id] -= rewards_threshold
            text += "

🎉 Has alcanzado 5 recargas. Puedes reclamar una licencia gratis."
        await query.edit_message_text(text)

    elif query.data == "admin":
        await query.edit_message_text("👨‍💻 Panel de administrador:
- Ver stock
- Agregar licencias
- Agregar afiliados
- Modificar productos")

# Configuración
def main():
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token("YOUR_TELEGRAM_BOT_TOKEN").build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.run_polling()

if __name__ == "__main__":
    main()
    