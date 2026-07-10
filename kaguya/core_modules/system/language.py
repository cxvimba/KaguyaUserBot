from pyrogram import Client
from pyrogram.types import Message
from kaguya.types import on_command
from kaguya.utils.prefix import get_prefix


@on_command(['language', 'lang', 'язык'])
async def change_language(self, client: Client, message: Message):
    """Динамически изменяет язык системы."""
    current_lang = client.get_lang()
    p = get_prefix(client)

    if len(message.command) < 2:
        await message.edit_text(
            self.get_text('lang_usage').format(current=current_lang, p=p)
        )
        return

    new_lang = message.command[1].strip().lower()
    if len(new_lang) != 2 or not new_lang.isalpha():
        await message.edit_text(
            self.get_text('lang_invalid')
        )
        return

    await client.set_lang(new_lang)
    await message.edit_text(
        self.get_text('lang_success').format(new_lang=new_lang)
    )
