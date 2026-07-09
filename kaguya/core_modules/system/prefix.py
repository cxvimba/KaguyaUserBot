from pyrogram import Client
from pyrogram.types import Message
from kaguya.types import on_command


@on_command(['prefix', 'префикс'])
async def change_prefix(self, client: Client, message: Message):
    """Динамически изменяет префиксы команд."""
    if len(message.command) < 2:
        current = ' '.join([f'<code>{p}</code>' for p in client.prefixes])
        await message.edit_text(
            self.get_text('prefix_usage').format(current=current, p=client.prefixes[0])
        )
        return

    new_prefixes = message.command[1:]
    clean_prefixes = list(set([p.strip() for p in new_prefixes if len(p.strip()) == 1]))

    if not clean_prefixes:
        await message.edit_text(self.get_text('prefix_invalid'))
        return

    settings = client.db.get_category('settings')
    await settings.set('prefixes', clean_prefixes)

    client.prefixes = clean_prefixes

    formatted = ', '.join([f'<code>{p}</code>' for p in clean_prefixes])
    await message.edit_text(
        self.get_text('prefix_success').format(formatted=formatted)
    )
