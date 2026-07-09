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

    text_tpl = self.get_text('assistant_welcome')
    await message.reply_text(
        text_tpl.format(
            mention=message.from_user.mention,
            owner=owner_username
        )
    )
