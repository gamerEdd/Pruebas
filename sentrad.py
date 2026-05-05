import random
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8397677956:AAEvuUPj5fkNcacFZjgx9A_YdgSMZjG5Px8"   # tu token
ADMIN_ID = 1196148306

suscriptores = set()

# --- Comandos para los usuarios ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Bienvenido al Bot de Señales de Trading.\n"
        "Usa /suscribirme para recibir señales 📊."
    )

async def suscribirme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    suscriptores.add(user_id)
    await update.message.reply_text("✅ Te has suscrito para recibir señales de trading.")
    print(f"[INFO] Usuario {user_id} suscrito.")

async def senal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ No tienes permiso para enviar señales.")
        return

    if not context.args or len(context.args) < 4:
        await update.message.reply_text(
            "Formato incorrecto.\nEjemplo:\n/senal EURUSD 1.0750 1.0800 1.0720"
        )
        return

    par, entrada, tp, sl = context.args[0:4]

    mensaje = (
        f"📢 Señal de Trading\n\n"
        f"📈 Par: {par}\n"
        f"➡️ Entrada: {entrada}\n"
        f"🎯 Take Profit: {tp}\n"
        f"🛑 Stop Loss: {sl}\n"
        f"⏰ TimeFrame: H1"
    )

    for uid in suscriptores:
        await context.bot.send_message(chat_id=uid, text=mensaje)

    print(f"[SEÑAL MANUAL] Enviada: {mensaje}")
    await update.message.reply_text("✅ Señal enviada a todos los suscriptores.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ No tienes permiso para enviar mensajes.")
        return

    if not context.args:
        await update.message.reply_text("Uso: /broadcast Tu mensaje aquí")
        return

    mensaje = " ".join(context.args)

    for uid in suscriptores:
        await context.bot.send_message(chat_id=uid, text=mensaje)

    print(f"[BROADCAST] Enviado: {mensaje}")
    await update.message.reply_text("✅ Mensaje enviado a todos los suscriptores.")

# --- Señales automáticas cada minuto ---
pares = ["EURUSD", "GBPUSD", "USDJPY", "BTCUSD", "ETHUSD"]

async def enviar_senal_automatica(context: ContextTypes.DEFAULT_TYPE):
    if not suscriptores:
        print("[INFO] No hay suscriptores, no se envió señal automática.")
        return

    par = random.choice(pares)
    entrada = round(random.uniform(1.0500, 1.1000), 4)
    tp = round(entrada + random.uniform(0.0020, 0.0050), 4)
    sl = round(entrada - random.uniform(0.0020, 0.0050), 4)

    mensaje = (
        f"🤖 Señal Automática de Prueba\n\n"
        f"📈 Par: {par}\n"
        f"➡️ Entrada: {entrada}\n"
        f"🎯 Take Profit: {tp}\n"
        f"🛑 Stop Loss: {sl}\n"
    )

    for uid in suscriptores:
        await context.bot.send_message(chat_id=uid, text=mensaje)

    print(f"[AUTO-SEÑAL] Enviada: {mensaje}")

    # después del mensaje de señal → enviar mensaje normal
    normal_msg = "📩 Mensaje normal de prueba."
    for uid in suscriptores:
        await context.bot.send_message(chat_id=uid, text=normal_msg)

    print(f"[AUTO-MENSAJE] Enviado: {normal_msg}")

# --- Main ---
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("suscribirme", suscribirme))
    app.add_handler(CommandHandler("senal", senal))
    app.add_handler(CommandHandler("broadcast", broadcast))

    # Programar señales automáticas cada 60 segundos
    job_queue = app.job_queue
    job_queue.run_repeating(enviar_senal_automatica, interval=60, first=5)

    print("🤖 Bot de Trading corriendo con señales automáticas...")
    app.run_polling()

if __name__ == "__main__":
    main()
