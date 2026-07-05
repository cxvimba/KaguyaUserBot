import aiohttp
import logging
from pyrogram import Client
from pyrogram.errors import BotInlineDisabled
from pyrogram.types import Message, InlineQuery
from kaguya.types import on_command, on_assistant_inline
from kaguya.utils.prefix import get_prefix


logger = logging.getLogger('Kaguya.SystemToken')


@on_command(['token', 'токен'])
async def set_token(self, client: Client, message: Message):
    """Проверяет и привязывает токен ассистента."""
    if len(message.command) < 2:
        p = get_prefix(client)
        await message.edit_text(
            f'⚙️ <b>Kaguya | Бот-ассистент</b>\n\n'
            f'Для работы инлайн-функционала и кнопок тебе нужен свой бот.\n\n'
            f'1. Зайди в @BotFather и создай бота\n'
            f'2. В настройках бота включи <b>Inline Mode</b> (<b>ОБЯЗАТЕЛЬНО!</b>)\n'
            f'3. В этом же меню поставь <b>Inline Feedback 100%</b>\n'
            f'4. Скопируй токен и напиши: <code>{p}token твой_токен_бота</code>'
        )
        return

    token = message.command[1].strip()
    await message.edit_text('⏳ <b>Kaguya:</b> Проверяю токен...')

    url = f'https://api.telegram.org/bot{token}/getMe'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    await message.edit_text('❌ <b>Kaguya:</b> Неверный токен! Сверься с @BotFather.')
                    return

                data = await response.json()
                bot_username = data['result']['username']

        settings = client.db.get_category('settings')
        await settings.set('bot_token', token)
        await settings.set('bot_username', bot_username)

        await message.edit_text('📥 <b>Kaguya:</b> Запуск ассистента...')
        await client.start_assistant(token)

        await message.edit_text('⚙️ <b>Kaguya:</b> Проверяю инлайн-функционал...')

        try:
            results = await client.get_inline_bot_results(bot_username, 'setup_check')
        except BotInlineDisabled:
            await client.stop_assistant()
            await settings.delete('bot_token')
            await settings.delete('bot_username')

            p = get_prefix(client)
            text = (
                f'⚠️ <b>Kaguya | Ошибка активации</b>\n\n'
                f'Токен верный, но у твоего ассистента @{bot_username} <b>ВЫКЛЮЧЕН инлайн-режим</b>!\n\n'
                f'Я прикрепила для тебя простую пошаговую инструкцию на картинке. '
                f'Как только включишь, пришли токен заново через <code>{p}token твой_токен_бота</code>!\n\n'
                f'🔗 BotFather: @BotFather'
            )

            await client.edit_media_cached(
                message=message,
                cache_key='inline_guide_file_id',
                local_path='assets/Kaguya_inline_guide.png',
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
        await message.edit_text(f'❌ <b>Kaguya:</b> Ошибка подключения к API Telegram: <code>{e}</code>')


@on_command(['token_rm', 'токен_удалить'])
async def remove_token(self, client: Client, message: Message):
    """Останавливает и отвязывает бота-ассистента."""
    settings = client.db.get_category('settings')

    bot_token = await settings.get('bot_token')
    if not bot_token:
        await message.edit_text('❌ <b>Kaguya:</b> Бот-ассистент и так не привязан.')
        return

    await message.edit_text('🗑 <b>Kaguya:</b> Остановка ассистента...')

    await client.stop_assistant()

    await settings.delete('bot_token')
    await settings.delete('bot_username')

    await message.edit_text(
        f'🗑 <b>Kaguya:</b> Бот-ассистент отвязан.\n\n'
        f'<blockquote>Инлайн функционал выключен.</blockquote>'
    )


@on_assistant_inline()
async def system_inline(self, client: Client, inline_query: InlineQuery):
    """Инлайн-обработчик для проверки привязки бота-ассистента."""
    query_text = inline_query.query
    if query_text != 'setup_check':
        return

    from pyrogram.types import (
        InlineQueryResultArticle, InputTextMessageContent,
        InlineKeyboardMarkup, InlineKeyboardButton
    )

    markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(
                text='👾 Перейти к боту',
                url=f'https://t.me/{client.me.username}')
            ]
        ]
    )

    results = [
        InlineQueryResultArticle(
            id='setup_ok',
            title='Kaguya | Ассистент готов!',
            description='Отправить подтверждение успешной настройки',
            input_message_content=InputTextMessageContent(
                f'🌸 <b>Kaguya | Бот-ассистент успешно привязан!</b>\n\n'
                f'<blockquote>Все инлайн-функции и интерактивные кнопки активны и готовы к работе.</blockquote>'
            ),
            reply_markup=markup
        )
    ]
    await inline_query.answer(results, cache_time=1)
