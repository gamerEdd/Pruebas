from telethon import TelegramClient, events
import asyncio

# -------------------- CONFIG --------------------
api_id = 29996698          # tu api_id de my.telegram.org
api_hash = 'e06645ea349492f75362d916bf1fd98e'
session_name = 'mi_sesion'  # Archivo de sesión guardado automáticamente

client = TelegramClient(session_name, api_id, api_hash)

# -------------------- FUNCIONES --------------------
async def listar_chats():
    print("📡 Listando todos los grupos y canales donde estás...")
    chats = []
    async for dialog in client.iter_dialogs():
        chats.append(dialog)
        print(f"Nombre: {dialog.name}, ID: {dialog.id}, Tipo: {type(dialog.entity).__name__}")
    return chats

async def elegir_chat():
    chats = await listar_chats()
    grupo_id = int(input("\nIngresa el ID del grupo/canal que quieres escuchar: "))
    return grupo_id

async def leer_ultimos_mensajes(grupo_id, cantidad=10):
    mensajes = await client.get_messages(grupo_id, limit=cantidad)
    if not mensajes:
        print("[INFO] No se encontraron mensajes.")
        return
    print(f"\n📨 Últimos {cantidad} mensajes del grupo/canal seleccionado:")
    for m in reversed(mensajes):
        print(f"[ULTIMO] UsuarioID {m.sender_id}: {m.message}")

async def escuchar_nuevos_mensajes(grupo_id):
    @client.on(events.NewMessage(chats=grupo_id))
    async def listener(event):
        print(f"[NUEVO] UsuarioID {event.sender_id}: {event.message.message}")

# -------------------- MAIN --------------------
async def main():
    await client.start()
    print("✅ Sesión iniciada correctamente.\n")

    grupo_id = await elegir_chat()
    await leer_ultimos_mensajes(grupo_id)
    print("\n📡 Ahora escuchando mensajes nuevos en tiempo real...\n")
    await escuchar_nuevos_mensajes(grupo_id)

    # Mantener corriendo
    await client.run_until_disconnected()

# -------------------- EJECUCIÓN --------------------
if __name__ == "__main__":
    asyncio.run(main())
