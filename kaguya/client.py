import os
import asyncio
import logging
import sys
from typing import Dict, List, Tuple, Any, Optional
from dotenv import load_dotenv
from pyrogram import Client, enums
from pyrogram.handlers import Handler, MessageHandler
from pyrogram.types import Message, InputMediaPhoto, InlineKeyboardMarkup, InputChatPhotoStatic, BotCommand
from kaguya.storage import KaguyaStorage
from kaguya.types import on_command


logger = logging.getLogger('Kaguya.Client')


class KaguyaClient(Client):
    """Клиент Kaguya."""
    def __init__(self):
        if not os.path.exists('data'):
            os.makedirs('data')
            
        try:
            load_dotenv()

            api_id_env = os.getenv('API_ID')
            api_hash_env = os.getenv('API_HASH')

            if not api_id_env or not api_hash_env:
                raise ValueError('API_ID или API_HASH не найдены в файле .env')

            api_id = int(api_id_env)
            api_hash = api_hash_env
        except Exception:
            # Авто .env
            if not os.path.exists('.env'):
                with open('.env', 'w', encoding='utf-8') as f:
                    f.write(
                        '# Настройки Kaguya UserBot\n'
                        '# Получи свои API_ID и API_HASH на сайте https://my.telegram.org/apps\n\n'
                        'API_ID=\n'
                        'API_HASH=\n'
                    )

            logger.error(
                f'\n'
                f'{"="*60}\n'
                f'⚠️  Kaguya | Ошибка конфигурации!\n\n'
                f'Я не нашла твои ключи API_ID или API_HASH в файле .env.\n'
                f'Я только что создала для тебя пустой файл .env в корне проекта.\n\n'
                f'Что тебе нужно сделать сейчас:\n'
                f'1. Открой появившийся файл .env в Блокноте\n'
                f'2. Зайди и авторизуйся на сайте my.telegram.org\n'
                f'3. Открой раздел «API development tools»\n'
                f'4. Заполните поле App title, например KaguyaApp\n'
                f'5. В поле Short name укажи короткое имя, например my_app\n'
                f'6. В поле URL вставь ссылку на свой телеграм аккаунт\n'
                f'7. Поле Platform укажи подходящий тип, например Desktop\n'
                f'8. Нажми кнопку Create application. (ВАЖНО: если вылезла ошибка, попробуй что-нибудь поменять или зайти со смартфона. Проблема в самом сайте.)\n'
                f'9. Cкопируй свои API_ID и API_HASH\n'
                f'10. Впиши их в файл .env после знака "=" (без пробелов) и сохрани\n'
                f'11. Запусти Kaguya заново через kaguya_run.bat!\n'
                f'{"="*60}\n'
            )
            sys.exit(1)

        session_path = os.path.join('data', 'kaguya')

        super().__init__(
            name=session_path,
            api_id=api_id,
            api_hash=api_hash,
            device_model='Kaguya OS',
            system_version='Windows 11',
            app_version='4.16.1',
            lang_code='ru',
            system_lang_code='ru-RU',
            client_platform=enums.ClientPlatform.DESKTOP
        )

        self.db = KaguyaStorage()
        self.loaded_modules: Dict[str, Any] = {}
        self.registered_handlers: Dict[str, List[Tuple[Handler, int]]] = {}

        self.assistant: Optional[Client] = None
        self.manager: Any = None
        self.prefixes: List[str] = ['.', '/']
        self.language: str = 'ru'


    def register_module_handler(self, module_name: str, handler: Handler, group: int = 0):
        """Метод регистрации хэндлера модуля в клиенте."""
        self.add_handler(handler, group)
        if module_name not in self.registered_handlers:
            self.registered_handlers[module_name] = []
        self.registered_handlers[module_name].append((handler, group))

    def unload_module_handler(self, module_name: str):
        """Метод выгрузки всех хэндлеров конкретного модуля."""
        handlers = self.registered_handlers.pop(module_name, [])
        for handler, group in handlers:
            try:
                self.remove_handler(handler, group)
            except Exception as e:
                logger.warning(f'Не удалось удалить хэндлер модуля {module_name}: {e}')


    async def start_assistant(self, token: str):
        """Инициализирует бота-ассистента, привязывает инлайн-обработчики."""
        if self.assistant:
            await self.stop_assistant()

        logger.info('Запуск бота-ассистента...')
        assistant = Client(
            name=os.path.join('data', 'kaguya_assistant'),
            api_id=self.api_id,
            api_hash=self.api_hash,
            bot_token=token
        )
        assistant.db = self.db
        self.assistant = assistant

        await assistant.start()

        settings = self.db.get_category('settings')
        updated_bot_profile = await settings.get('updated_bot_profile')

        if not updated_bot_profile:
            try:
                await settings.set('updated_bot_profile', True, 2*24*60*60)  # 48 часов во избежание флуда
                await assistant.set_bot_name('Kaguya | Assistant')

                short_desc = 'Интерактивный бот-помощник Kaguya 👾'
                if self.me.username:
                    short_desc += f'\nВладелец: @{self.me.username}'

                await assistant.set_bot_info_short_description(short_desc)

                await assistant.set_bot_info_description(
                    '🌸 Привет! Я интерактивный бот-помощник ЮзерБота Kaguya.\n\n'
                    'Я помогаю своему владельцу автоматизировать рутину.'
                )

                avatar_path = 'assets/Kaguya_icon.png'
                if os.path.exists(avatar_path):
                    await assistant.set_profile_photo(
                        photo=InputChatPhotoStatic(avatar_path)
                    )

                await assistant.set_bot_commands(
                    commands=[
                        BotCommand(
                            command='start',
                            description='ℹ️ Информация'
                        )
                    ]
                )

                logger.info('Профиль бота-ассистента успешно обновлен!')
            except Exception as set_err:
                logger.warning(f'Не удалось полностью настроить профиль ассистента: {set_err}')
        else:
            logger.info('Обновление профиля бота-ассистента пропущено.')

        if self.manager:
            self.manager.register_assistant_handlers(assistant)

    async def stop_assistant(self):
        """Останавливает и отвязывает бота-ассистента."""
        if self.assistant:
            logger.info('Остановка бота-ассистента...')
            await self.assistant.stop()
            self.assistant = None


    async def edit_media_cached(
        self, message: Message, cache_key: str, local_path: str,
        caption: str, reply_markup: Optional[InlineKeyboardMarkup] = None
    ) -> Message:
        """Редактирует и кэширует медиа-сообщение."""
        photo_cache = self.db.get_category('media-cache')
        cached_file_id = await photo_cache.get(cache_key)
        media_source = cached_file_id if cached_file_id else local_path

        try:
            res = await message.edit_media(
                media=InputMediaPhoto(
                    media=media_source,
                    caption=caption
                ),
                reply_markup=reply_markup
            )
            if not cached_file_id:
                new_file_id = res.photo.file_id
                await photo_cache.set(cache_key, new_file_id)
                logger.info(f'Медиа-файл для "{cache_key}" успешно кэширован: {new_file_id}')
            return res
        except Exception as media_error:
            if cached_file_id:
                logger.warning(f'Кэшированный File ID для "{cache_key}" устарел: {media_error}. Перезапись...')
                await photo_cache.delete(cache_key)
                res = await message.edit_media(
                    media=InputMediaPhoto(
                        media=local_path,
                        caption=caption
                    ),
                    reply_markup=reply_markup
                )
                await photo_cache.set(cache_key, res.photo.file_id)
                return res
            else:
                raise media_error


    def register_core_handlers(self):
        """Регистрация системных хэндлеров."""
        @on_command(['kaguya', 'кагуя', 'menu', 'меню'])
        async def core_menu_callback(client: Client, message: Message):
            try:
                settings = client.db.get_category('settings')

                if client.assistant:
                    bot_username = await settings.get('bot_username', 'Unknown')
                    assistant_status = f'@{bot_username}'
                else:
                    assistant_status = 'Не привязан'

                prefixes_str = ' '.join([f'<code>{p}</code>' for p in client.prefixes])
                modules_count = len(client.loaded_modules)

                text = (
                    f'🌸 <b>Kaguya UserBot</b>\n\n'
                    f'Привет, «{client.me.mention}»!\n'
                    f'Я твой виртуальный ассистент <b>Kaguya</b> 👾\n\n'
                    f'<blockquote expandable>Я помогаю автоматизировать рутину. '
                    f'Моя главная сила — <b>абсолютная модульность</b>: ты можешь расширять мой функционал, '
                    f'устанавливая собственные модули <b>на лету</b> прямо из чата!</blockquote>\n\n'
                    f'ℹ️ <b>Информация о системе:</b>\n'
                    f' ├ <b>Версия:</b> <code>1.0.0</code>\n'
                    f' ├ <b>Префиксы:</b> {prefixes_str}\n'
                    f' ├ <b>Ассистент-помощник:</b> {assistant_status}\n'
                    f' └ <b>Загружено модулей:</b> <code>{modules_count}</code>\n\n'
                    f'💡 <i>Напиши <code>{client.prefixes[0]}модули</code> для просмотра модулей.</i>'
                )

                await client.edit_media_cached(
                    message=message,
                    cache_key='main_menu_file_id',
                    local_path='assets/Kaguya_main.png',
                    caption=text
                )
                return
            except Exception as e:
                logger.error(f'Ошибка в главном меню ядра: {e}', exc_info=True)

        menu_filter = getattr(core_menu_callback, '__kaguya_filter__')
        self.register_module_handler('core_system', MessageHandler(core_menu_callback, menu_filter))


    async def start_kaguya(self):
        """Запускает жизненный цикл Kaguya."""
        logger.info('Запуск Kaguya ЮзерБота...')
        async with self:
            from kaguya.loader import ModuleManager
            self.manager = ModuleManager(self)

            settings = self.db.get_category('settings')
            self.prefixes = await settings.get('prefixes', ['.', '/'])
            self.language = await settings.get('language', 'ru')

            logger.info(f'Активные префиксы команд: {self.prefixes}')
            logger.info(f'Текущий язык системы: {self.language}')

            await settings.set('owner_id', self.me.id)

            self.register_core_handlers()

            bot_token = await settings.get('bot_token')
            if bot_token:
                try:
                    await self.start_assistant(bot_token)
                    logger.info(f'Бот-ассистент @{await settings.get("bot_username")} успешно запущен!')
                except Exception as e:
                    logger.error(f'Не удалось запустить бота-ассистента: {e}', exc_info=True)

            logger.info('Загрузка модулей...')
            self.manager.load_all_modules()

            logger.info('Kaguya успешно запущена и готова к работе!')

            try:
                lang = await settings.get('language', 'ru')
                start_texts = {
                    'ru': (
                        '🌸 <b>Kaguya UserBot успешно запущена!</b>\n\n'
                        '👾 Напиши <code>.kaguya</code> в любом чате для вызова меню.\n'
                        '⚙️ Изменить язык интерфейса: <code>.lang en</code>'
                    ),
                    'en': (
                        '🌸 <b>Kaguya UserBot successfully started!</b>\n\n'
                        '👾 Type <code>.kaguya</code> in any chat to open the menu.\n'
                        '⚙️ Change interface language: <code>.lang ru</code>'
                    )
                }
                welcome_text = start_texts.get(lang, start_texts['ru'])
                await self.send_message('me', welcome_text)
                logger.info('Уведомление о старте отправлено в Избранное.')
            except Exception as send_err:
                logger.warning(f'Не удалось отправить приветственное сообщение: {send_err}')

            try:
                while True:
                    await asyncio.sleep(1)
            finally:
                await self.stop_assistant()


    def get_lang(self) -> str:
        """Возвращает текущий язык системы."""
        return self.language

    async def set_lang(self, lang: str):
        """Обновляет язык системы."""
        self.language = lang
        settings = self.db.get_category('settings')
        await settings.set('language', lang)


    async def set_fsm(self, state: str, data: Optional[dict] = None):
        """Устанавливает состояние FSM."""
        settings = self.db.get_category('settings')
        await settings.set('fsm_state', state)
        await settings.set('fsm_data', data or {})

    async def get_fsm_state(self) -> Optional[str]:
        """Возвращает состояние FSM."""
        settings = self.db.get_category('settings')
        return await settings.get('fsm_state')

    async def get_fsm_data(self) -> dict:
        """Возвращает данные FSM."""
        settings = self.db.get_category('settings')
        return await settings.get('fsm_data', {})

    async def clear_fsm(self):
        """Сбрасывает состояние FSM."""
        settings = self.db.get_category('settings')
        await settings.delete('fsm_state')
        await settings.delete('fsm_data')
