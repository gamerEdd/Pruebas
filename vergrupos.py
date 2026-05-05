from telethon import TelegramClient

# Datos de tu app en my.telegram.org
api_id = 29996698
api_hash = 'e06645ea349492f75362d916bf1fd98e'

client = TelegramClient('mi_sesion', api_id, api_hash)

async def listar_chats():
    async for dialog in client.iter_dialogs():
        print(f"Nombre: {dialog.name}, ID: {dialog.id}, Tipo: {dialog.entity.__class__.__name__}")

with client:
    client.loop.run_until_complete(listar_chats())
