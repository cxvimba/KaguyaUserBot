import aiohttp
import uuid
import urllib.parse
from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, \
    InputTextMessageContent, CallbackQuery, InlineQuery
from kaguya.types import BaseModule, ModuleInfo, on_command, on_assistant_inline, on_assistant_callback
from kaguya.utils.prefix import get_prefix


LANGS = [
    [('🇷🇺 RU', 'ru'), ('🇺🇸 EN', 'en'), ('🇪🇸 ES', 'es'), ('🇩🇪 DE', 'de'), ('🇫🇷 FR', 'fr')],
    [('🇮🇹 IT', 'it'), ('🇵🇹 PT', 'pt'), ('🇯🇵 JA', 'ja'), ('🇨🇳 ZH', 'zh'), ('🇰🇷 KO', 'ko')],
    [('🇹🇷 TR', 'tr'), ('🇺🇦 UK', 'uk'), ('🇵🇱 PL', 'pl'), ('🇸🇪 SV', 'sv'), ('🇳🇱 NL', 'nl')],
    [('🇮🇩 ID', 'id'), ('🇹🇭 TH', 'th'), ('🇻🇳 VI', 'vi'), ('🇮🇳 HI', 'hi'), ('🇸🇦 AR', 'ar')],
    [('🇬🇷 EL', 'el'), ('🇮🇷 FA', 'fa'), ('🇮🇱 HE', 'he'), ('🇷🇴 RO', 'ro'), ('🇫🇮 FI', 'fi')]
]


class TranslatorModule(BaseModule):
    meta = ModuleInfo(
        name='Переводчик',
        description='Переводчик текста через инлайн-ассистента',
        version='1.1.0',
        author='cxvimba',
        commands={
            'tr | переводчик | translate': 'Запустить интерактивный перевод'
        }
    )

    LANGUAGES = {
        'en': {
            'usage': (
                'ℹ️ <b>Kaguya | Translator</b>\n\n'
                '• Reply to a message with <code>{p}tr</code>\n'
                '• Or type: <code>{p}tr Text for translation</code>'
            ),
            'assistant_required': (
                '⚙️ <b>Kaguya | Helper Bot</b>\n\n'
                'You need your own bot for this module.\n\n'
                '1. Go to @BotFather and create a bot\n'
                '2. Turn on <b>Inline Mode</b> in Bot Settings (<b>REQUIRED!</b>)\n'
                '3. Copy the token and run: <code>{p}token YOUR_BOT_TOKEN</code>'
            ),
            'inline_title': 'Translation: {preview}',
            'inline_desc': 'Select target language from the flags below',
            'original_text_title': '🌐 <b>Kaguya | Translator</b>\n └ 📝 <b>Original Text:</b>\n\n{text}',
            'alert_not_owner': '💢 Kaguya: Hey, this is not your control panel!',
            'alert_cache_lost': '❌ Kaguya: Error — text lost from cache!',
            'alert_translating': '⏳ Kaguya: Translating...',
            'alert_api_error': '❌ Kaguya: Translator API error: {status}',
            'alert_generic_error': '❌ Kaguya: Error translating text: <code>{error}</code>',
            'result_title': '🌐 <b>Kaguya | Translator ({sl} ➔ {tl}):</b>\n └ 📝 {text}'
        },
        'ru': {
            'usage': (
                'ℹ️ <b>Kaguya | Переводчик</b>\n\n'
                '• Ответь на сообщение командой <code>{p}tr</code>\n'
                '• Или напишите: <code>{p}tr Текст для перевода</code>'
            ),
            'assistant_required': (
                '⚙️ <b>Kaguya | Бот-ассистент</b>\n\n'
                'Для этого модуля нужен свой бот.\n\n'
                '1. Зайди в @BotFather и создай бота\n'
                '2. В настройках бота включи <b>Inline Mode</b> (<b>ОБЯЗАТЕЛЬНО!</b>)\n'
                '3. Скопируй токен и напиши: <code>{p}token твой_токен_бота</code>'
            ),
            'inline_title': 'Перевод текста: {preview}',
            'inline_desc': 'Выбери язык на панели флагов ниже',
            'original_text_title': '🌐 <b>Kaguya | Переводчик</b>\n └ 📝 <b>Исходный текст:</b>\n\n{text}',
            'alert_not_owner': '💢 Kaguya: Эй, это не твоя панель управления!',
            'alert_cache_lost': '❌ Kaguya: Ошибка — текст утерян из кэша!',
            'alert_translating': '⏳ Kaguya: Перевожу...',
            'alert_api_error': '❌ Kaguya: Переводчик отправил ошибку: {status}',
            'alert_generic_error': '❌ Kaguya: Ошибка при переводе текста: <code>{error}</code>',
            'result_title': '🌐 <b>Kaguya | Переводчик ({sl} ➔ {tl}):</b>\n └ 📝 {text}'
        }
    }

    @on_command(['tr', 'перевод', 'translate'])
    async def translate_cmd(self, client: Client, message: Message):
        """Переводит текст."""
        target_text = ''
        reply = message.reply_to_message

        if reply:
            target_text = reply.text or reply.caption

        elif len(message.command) > 1:
            target_text = message.text.split(maxsplit=1)[1]

        p = get_prefix(client)
        if not target_text:
            await message.edit_text(
                self.get_text('usage').format(p=p)
            )
            return

        if not client.assistant:
            await message.edit_text(
                self.get_text('assistant_required').format(p=p)
            )
            return

        settings = client.db.get_category('settings')
        bot_username = await settings.get('bot_username')

        tr_key = str(uuid.uuid4())[:8]
        cache = client.db.get_category('tr_cache')
        await cache.set(tr_key, target_text, expire=3600)

        results = await client.get_inline_bot_results(bot_username, f'tr_{tr_key}')

        await client.send_inline_bot_result(
            chat_id=message.chat.id,
            query_id=results.query_id,
            result_id=results.results[0].id
        )

        await message.delete()

    @on_assistant_inline('tr_')
    async def translator_inline(self, client: Client, inline_query: InlineQuery):
        """Отвечает инлайн-результатом с сеткой флагов."""
        query_text = inline_query.query
        tr_key = query_text[3:]
        cache = client.db.get_category('tr_cache')
        original_text = await cache.get(tr_key)

        if not original_text:
            return

        keyboard_rows = []
        for row in LANGS:
            row_buttons = []
            for text, lang in row:
                row_buttons.append(
                    InlineKeyboardButton(
                        text=text,
                        callback_data=f'tr_{lang}_{tr_key}'
                    )
                )
            keyboard_rows.append(row_buttons)

        markup = InlineKeyboardMarkup(keyboard_rows)

        preview_text = original_text[:50] + '...' if len(original_text) > 50 else original_text
        results = [
            InlineQueryResultArticle(
                id=tr_key,
                title=self.get_text('inline_title').format(preview=preview_text),
                description=self.get_text('inline_desc'),
                input_message_content=InputTextMessageContent(
                    self.get_text('original_text_title').format(text=original_text)
                ),
                reply_markup=markup
            )
        ]

        await inline_query.answer(results, cache_time=1)

    @on_assistant_callback('tr_')
    async def translator_callback(self, client: Client, callback_query: CallbackQuery):
        """Выполняет перевод при клике на флаг с защитой от чужаков."""
        settings = client.db.get_category('settings')
        owner_id = await settings.get('owner_id')

        if callback_query.from_user.id != owner_id:
            await callback_query.answer(
                text=self.get_text('alert_not_owner'),
                show_alert=True
            )
            return

        parts = callback_query.data.split("_")
        target_lang = parts[1]
        tr_key = parts[2]

        cache = client.db.get_category('tr_cache')
        original_text = await cache.get(tr_key)

        if not original_text:
            await callback_query.answer(
                text=self.get_text('alert_cache_lost'),
                show_alert=True
            )
            return

        await callback_query.answer(
            text=self.get_text('alert_translating')
        )

        encoded_text = urllib.parse.quote(original_text)
        url = f'https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={encoded_text}'

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        await callback_query.answer(
                            text=self.get_text('alert_api_error').format(status=response.status),
                            show_alert=True
                        )
                        return

                    data = await response.json()
                    translated_sentences = []
                    for sentence in data[0]:
                        if sentence[0]:
                            translated_sentences.append(sentence[0])

                    translated_text = ''.join(translated_sentences)
                    detected_lang = data[2]

                    await client.edit_inline_text(
                        inline_message_id=callback_query.inline_message_id,
                        text=self.get_text('result_title').format(
                            sl=detected_lang.upper(),
                            tl=target_lang.upper(),
                            text=translated_text
                        ),
                        reply_markup=callback_query.message.reply_markup if callback_query.message else None
                    )

        except Exception as e:
            await callback_query.answer(
                text=self.get_text('alert_generic_error').format(error=e),
                show_alert=True
            )
