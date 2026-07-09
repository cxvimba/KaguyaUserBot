import os
import aiohttp
import logging
from pyrogram import Client
from pyrogram.errors import BotInlineDisabled
from pyrogram.types import Message, InlineQuery, InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultArticle, \
    InputTextMessageContent
from kaguya.types import on_command, on_assistant_inline
from kaguya.utils.prefix import get_prefix


logger = logging.getLogger('Kaguya.SystemToken')


@on_command(['token', 'токен'])
async def set_token(self, client: Client, message: Message):
    """Проверяет и привязывает токен ассистента."""
    p = get_prefix(client)
    if len(message.command) < 2:
        await message.edit_text(
            self.get_text('token_usage').format(p=p)
        )
        return

    token = message.command[1].strip()
    await message.edit_text(self.get_text('token_checking'))

    url = f'https://api.telegram.org/bot{token}/getMe'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    await message.edit_text(self.get_text('token_invalid'))
                    return

                data = await response.json()
                bot_username = data['result']['username']

        settings = client.db.get_category('settings')
        await settings.set('bot_token', token)
        await settings.set('bot_username', bot_username)

        await message.edit_text(self.get_text('token_starting'))
        await client.start_assistant(token)

        await message.edit_text(self.get_text('token_checking_inline'))

        try:
            results = await client.get_inline_bot_results(bot_username, 'setup_check')
        except BotInlineDisabled:
            await client.stop_assistant()
            await settings.delete('bot_token')
            await settings.delete('bot_username')

            text = self.get_text('token_inline_disabled').format(bot_username=bot_username, p=p)

            lang = client.get_lang()
            local_path = f'assets/Kaguya_inline_guide_{lang}.png'

            if not os.path.exists(local_path):
                local_path = 'assets/Kaguya_inline_guide_ru.png'

            cache_key = f'inline_guide_file_id_{lang}'

            await client.edit_media_cached(
                message=message,
                cache_key=cache_key,
                local_path=local_path,
                caption=text
            )
            return

        await client.send_inline_bot_result(
            chat_id=message.chat.id,
            query_id=results.query_id,
            result_id=results.results[0].id
        )
        await message.delete()

    except Exception as e:
        await message.edit_text(
            self.get_text('token_api_error').format(error=e)
        )


@on_command(['token_rm', 'токен_удалить'])
async def remove_token(self, client: Client, message: Message):
    """Останавливает и отвязывает бота-ассистента."""
    settings = client.db.get_category('settings')

    bot_token = await settings.get('bot_token')
    if not bot_token:
        await message.edit_text(self.get_text('token_rm_not_bound'))
        return

    await message.edit_text(self.get_text('token_rm_stopping'))

    await client.stop_assistant()

    await settings.delete('bot_token')
    await settings.delete('bot_username')

    await message.edit_text(self.get_text('token_rm_success'))


@on_assistant_inline('setup_check')
async def system_inline(self, client: Client, inline_query: InlineQuery):
    """Инлайн-обработчик для проверки привязки бота-ассистента."""
    markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(
                text=self.get_text('inline_go_to_bot'),
                url=f'https://t.me/{client.me.username}')
            ]
        ]
    )

    results = [
        InlineQueryResultArticle(
            id='setup_ok',
            title=self.get_text('inline_setup_ok_title'),
            description=self.get_text('inline_setup_ok_desc'),
            input_message_content=InputTextMessageContent(
                self.get_text('inline_setup_ok_text')
            ),
            reply_markup=markup
        )
    ]
    await inline_query.answer(results, cache_time=1)
