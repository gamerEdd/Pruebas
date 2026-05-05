from telethon import TelegramClient, events

# -------------------- CONFIG --------------------
api_id = 29996698
api_hash = 'e06645ea349492f75362d916bf1fd98e'
telefono = '+593968619722'
session_name = 'mi_sesion'

# Crear cliente
client = TelegramClient(session_name, api_id, api_hash)

# -------------------- FUNCIONES --------------------
def listar_chats():
    print("📡 Listando todos los grupos y canales donde estás...\n")
    chats = []
    for dialog in client.iter_dialogs():
        chats.append(dialog)
        print(f"Nombre: {dialog.name}, ID: {dialog.id}, Tipo: {type(dialog.entity).__name__}")
    return chats

def elegir_chat(chats):
    grupo_id = int(input("\nIngresa el ID del grupo/canal que quieres escuchar: "))
    return grupo_id

async def leer_ultimos_mensajes_async(grupo_id, cantidad=10):
    mensajes = await client.get_messages(grupo_id, limit=cantidad)
    if not mensajes:
        print("[INFO] No se encontraron mensajes.")
        return
    print(f"\n📨 Últimos {cantidad} mensajes del grupo/canal seleccionado:")
    for m in reversed(mensajes):
        print(f"[ULTIMO] UsuarioID {m.sender_id}: {m.message}")

def escuchar_nuevos_mensajes(grupo_id):
    @client.on(events.NewMessage(chats=grupo_id))
    async def listener(event):
        print(f"[NUEVO] UsuarioID {event.sender_id}: {event.message.message}")

# -------------------- EJECUCIÓN --------------------
with client:
    print("✅ Sesión iniciada correctamente.\n")

    # Listar chats
    chats = listar_chats()

    # Elegir grupo/canal
    grupo_id = elegir_chat(chats)

    # Leer últimos 10 mensajes (usando coroutine con run_until_complete)
    client.loop.run_until_complete(leer_ultimos_mensajes_async(grupo_id))

    # Escuchar mensajes nuevos
    print("\n📡 Ahora escuchando mensajes nuevos en tiempo real...\n")
    escuchar_nuevos_mensajes(grupo_id)

    # Mantener corriendo
    client.run_until_disconnected()
