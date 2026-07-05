from pyrogram import Client
from pyrogram.types import Message
from kaguya.types import on_assistant_command


@on_assistant_command('start')
async def assistant_start(self, client: Client, message: Message):
    """Обработчик команды /start."""
    settings = self.client.db.get_category('settings')
    owner_id = await settings.get('owner_id')

    owner = await self.client.get_users(owner_id)
    owner_username = f'@{owner.username}' if owner.username else owner.mention

    await message.reply_text(
        f'🌸 <b>Kaguya | Ассистент</b>\n\n'
        f'Привет, «{message.from_user.mention}»!\n'
        f'Я интерактивный бот-помощник ЮзерБота <b>Kaguya</b> 👾\n\n'
        f'Мой владелец: {owner_username}\n'
        f'Я помогаю ему автоматизировать рутину.\n\n'
        f'💡 <i>Напиши <code>.kaguya</code> для вызова <b>Kaguya</b></i>.'
    )
