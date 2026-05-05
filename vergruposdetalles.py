from telethon import TelegramClient, types
import asyncio

api_id = 29996698
api_hash = 'e06645ea349492f75362d916bf1fd98e'
session_name = 'mi_sesion'

client = TelegramClient(session_name, api_id, api_hash)

# ID o username del grupo/canal
grupo_objetivo = -1003016944954  # o '@FUZION_x_NOA_Official'

async def main():
    await client.start()
    print("📡 Conectado a Telegram...")

    # Obtener la entidad completa del grupo/canal
    entity = await client.get_entity(grupo_objetivo)

    # Mostrar características principales
    print("✅ Información del grupo/canal:")
    print(f"Nombre: {entity.title if hasattr(entity, 'title') else entity.username}")
    print(f"ID: {entity.id}")
    print(f"Tipo: {type(entity).__name__}")
    print(f"Accesibilidad (publico/privado): {entity.megagroup if hasattr(entity, 'megagroup') else 'N/A'}")
    print(f"Miembros (si aplica): {getattr(entity, 'participants_count', 'N/A')}")
    print(f"Username: {getattr(entity, 'username', 'N/A')}")
    print(f"Is Broadcast (canal solo lectura): {getattr(entity, 'broadcast', 'N/A')}")
    print(f"Restricciones: {getattr(entity, 'restricted', 'N/A')}")

asyncio.run(main())
