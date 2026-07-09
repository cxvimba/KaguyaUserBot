from kaguya.types import BaseModule, ModuleInfo
from .modules import list_modules, install_module, unload_module
from .token import set_token, remove_token, system_inline
from .prefix import change_prefix
from .assistant import assistant_start
from .language import change_language


class SystemModule(BaseModule):
    meta = ModuleInfo(
        name='Система',
        description='Встроенные системные команды для Kaguya',
        version='1.1.0',
        author='cxvimba',
        commands={
            'modules | модули': 'Показать список всех активных модулей',
            'install | установить': 'Установить модуль (ответом на .py, .txt или .zip)',
            'unload | удалить': 'Выгрузить модуль из памяти',
            'prefix | префикс': 'Изменить префиксы команд',
            'token | токен': 'Привязать бота-ассистента для инлайн-кнопок',
            'token_rm | токен_удалить': 'Отвязать бота-ассистента',
            'lang | язык': 'Изменить язык системы'
        }
    )

    LANGUAGES = {
        'en': {
            'author': "Author",
            'commands': "Commands",
            'none': "none",

            'assistant_welcome': (
                '🌸 <b>Kaguya | Assistant</b>\n\n'
                'Hello, «{mention}»!\n'
                'I am an interactive helper bot for the <b>Kaguya</b> UserBot 👾\n\n'
                'My owner: {owner}\n'
                'I help them automate daily routines.\n\n'
                '💡 <i>Type <code>.kaguya</code> to trigger <b>Kaguya</b>.</i>'
            ),

            'no_modules': '⚠️ <b>Kaguya:</b> No loaded modules found.',
            'module_not_found': '❌ <b>Kaguya:</b> Module «{target_name}» not found.',
            'modules_header': '⚡️ <b>Kaguya UserBot</b> | 🌟 Modules: <code>{count}</code>\n\n',
            'modules_footer': '<blockquote>💡 Learn more about a module: <code>{p}modules ModuleName</code></blockquote>',

            'install_reply_to': '❌ <b>Kaguya:</b> Reply with this command to a module file (.py, .txt, or .zip).',
            'install_supported_formats': '❌ <b>Kaguya:</b> Only <code>.py</code>, <code>.txt</code>, or <code>.zip</code> files are supported.',
            'install_downloading': '📥 <b>Kaguya:</b> Downloading and checking module...',
            'install_damaged_zip': '❌ <b>Kaguya:</b> Damaged or insecure ZIP archive: <code>{error}</code>',
            'install_missing_init': '❌ <b>Kaguya:</b> <code>__init__.py</code> was not found inside the ZIP archive.',
            'install_invalid_structure': '❌ <b>Kaguya:</b> Invalid archive structure. Folder with <code>__init__.py</code> expected.',
            'install_reserved_name': '❌ <b>Kaguya:</b> Module name «{module_name}» is reserved by the system core.',
            'install_suspicious_code': (
                '⚠️ <b>Kaguya | Suspicious Module!</b>\n\n'
                'Banned system calls detected in package code: <code>{warnings}</code>\n'
                'This file might contain malicious code!\n\n'
                '<b>Installation has been blocked for security reasons.</b>'
            ),
            'install_author_conflict': (
                '❌ <b>Kaguya | Author Conflict</b>\n\n'
                'Module «{name}» is already installed, but its author is <b>{old_author}</b>.\n'
                'The new module is written by <b>{new_author}</b>.\n\n'
                'Installation blocked to prevent overwrite. If you want to replace it, '
                'delete the old one first: <code>{p}unload {name}</code>'
            ),
            'install_updating': '🔄 <b>Kaguya:</b> Updating module «{name}» to v{version}...',
            'install_success_package': (
                '✅ <b>Package module installed successfully!</b>\n\n'
                '📦 <b>{name}</b> <code>v{version}</code>\n'
                ' ├ <i>{description}</i>\n'
                ' └ Directory: <code>kaguya/modules/{module_name}</code>'
            ),
            'install_success_single': (
                '✅ <b>Module installed successfully!</b>\n\n'
                '📦 <b>{name}</b> <code>v{version}</code>\n'
                ' ├ <i>{description}</i>\n'
                ' └ <b>Commands:</b> {cmds}'
            ),
            'install_damaged_syntax': '❌ <b>Kaguya:</b> Damaged module syntax:\n<code>{error}</code>',
            'install_failed': '❌ <b>Kaguya:</b> Failed to load module:\n<code>{error}</code>',

            'unload_usage': '❌ <b>Kaguya:</b> Specify module name. Example: <code>.unload ModuleName</code>',
            'unload_not_found': '❌ <b>Kaguya:</b> Module named «{target_name}» not found.',
            'unload_core_protected': '❌ <b>Kaguya:</b> Core system modules cannot be unloaded.',
            'unload_success': '🗑 <b>Kaguya:</b> Module «{name}» successfully deleted.',
            'unload_error': '❌ <b>Kaguya:</b> Error deleting module:\n<i>{error}</i>',

            'prefix_usage': (
                '⚙️ <b>Kaguya | Prefix Settings</b>\n\n'
                '#️⃣ Current prefixes: {current}\n'
                ' └ Example: <code>{p}prefix . !</code>'
            ),
            'prefix_invalid': '❌ <b>Kaguya:</b> Prefix must consist of exactly one character!',
            'prefix_success': '✅ <b>Kaguya:</b> Command prefixes successfully changed to: {formatted}',

            'token_usage': (
                '⚙️ <b>Kaguya | Helper Bot</b>\n\n'
                'You need your own bot for inline features and interactive buttons.\n\n'
                '1. Go to @BotFather and create a bot\n'
                '2. Turn on <b>Inline Mode</b> in Bot Settings (<b>REQUIRED!</b>)\n'
                '3. Set <b>Inline Feedback to 100%</b> in the same menu\n'
                '4. Copy the token and run: <code>{p}token YOUR_BOT_TOKEN</code>'
            ),
            'token_checking': '⏳ <b>Kaguya:</b> Checking token...',
            'token_invalid': '❌ <b>Kaguya:</b> Invalid token! Please double check with @BotFather.',
            'token_starting': '📥 <b>Kaguya:</b> Initializing helper bot...',
            'token_checking_inline': '⚙️ <b>Kaguya:</b> Checking inline features...',
            'token_inline_disabled': (
                '⚠️ <b>Kaguya | Activation Error</b>\n\n'
                'Token is valid, but your helper bot @{bot_username} has <b>Inline Mode DISABLED</b>!\n\n'
                'We attached a step-by-step instruction on the image. '
                'Once enabled, resend your token using <code>{p}token YOUR_BOT_TOKEN</code>!\n\n'
                '🔗 BotFather: @BotFather'
            ),
            'token_api_error': '❌ <b>Kaguya:</b> Error connecting to Telegram API: <code>{error}</code>',
            'token_rm_not_bound': '❌ <b>Kaguya:</b> Helper bot is not bound.',
            'token_rm_stopping': '🗑 <b>Kaguya:</b> Stopping helper bot...',
            'token_rm_success': (
                '🗑 <b>Kaguya:</b> Helper bot has been unbound.\n\n'
                '<blockquote>Inline features are now disabled.</blockquote>'
            ),
            'inline_go_to_bot': '👾 Open Bot',
            'inline_setup_ok_title': 'Kaguya | Assistant is ready!',
            'inline_setup_ok_desc': 'Send setup confirmation message',
            'inline_setup_ok_text': (
                '🌸 <b>Kaguya | Helper bot successfully bound!</b>\n\n'
                '<blockquote>All inline features and interactive buttons are active and ready.</blockquote>'
            ),

            'lang_usage': (
                '⚙️ <b>Kaguya | Language Settings</b>\n\n'
                '🌐 Current language: <code>{current}</code>\n'
                ' ├ Supported languages depend on modules (e.g., <code>ru</code>, <code>en</code>).\n'
                ' └ Change: <code>{p}lang ru</code>'
            ),
            'lang_invalid': "❌ <b>Kaguya:</b> Language code must be exactly 2 letters (e.g., <code>ru</code> or <code>en</code>)!",
            'lang_success': "✅ <b>Kaguya:</b> System language successfully changed to: <code>{new_lang}</code>"
        },

        'ru': {
            'author': "Автор",
            'commands': "Команды",
            'none': "отсутствуют",

            'assistant_welcome': (
                '🌸 <b>Kaguya | Ассистент</b>\n\n'
                'Привет, «{mention}»!\n'
                'Я интерактивный бот-помощник ЮзерБота <b>Kaguya</b> 👾\n\n'
                'Мой владелец: {owner}\n'
                'Я помогаю ему автоматизировать рутину.\n\n'
                '💡 <i>Напиши <code>.kaguya</code> для вызова <b>Kaguya</b></i>.'
            ),

            'no_modules': '⚠️ <b>Kaguya:</b> Нет загруженных модулей.',
            'module_not_found': '❌ <b>Kaguya:</b> Модуль «{target_name}» не найден.',
            'modules_header': '⚡️ <b>Kaguya UserBot</b> | 🌟 Модули: <code>{count}</code>\n\n',
            'modules_footer': '<blockquote>💡 Узнать больше о модуле: <code>{p}modules ИмяМодуля</code></blockquote>',

            'install_reply_to': '❌ <b>Kaguya:</b> Ответь этой командой на файл модуля (.py, .txt или .zip).',
            'install_supported_formats': '❌ <b>Kaguya:</b> Поддерживаются только файлы <code>.py</code>, <code>.txt</code> или <code>.zip</code>.',
            'install_downloading': '📥 <b>Kaguya:</b> Скачиваю и проверяю модуль...',
            'install_damaged_zip': '❌ <b>Kaguya:</b> Поврежденный или опасный ZIP-архив: <code>{error}</code>',
            'install_missing_init': '❌ <b>Kaguya:</b> Внутри ZIP-архива не найден файл <code>__init__.py</code>.',
            'install_invalid_structure': '❌ <b>Kaguya:</b> Неверная структура архива. Ожидалась папка с <code>__init__.py</code>.',
            'install_reserved_name': '❌ <b>Kaguya:</b> Имя модуля «{module_name}» зарезервировано системой.',
            'install_suspicious_code': (
                '⚠️ <b>Kaguya | Подозрительный модуль!</b>\n\n'
                'В коде пакета обнаружены заблокированные вызовы: <code>{warnings}</code>\n'
                'Этот архив может содержать вредоносный код!\n\n'
                '<b>Установка заблокирована из соображений безопасности.</b>'
            ),
            'install_author_conflict': (
                '❌ <b>Kaguya | Конфликт авторов</b>\n\n'
                'Модуль «{name}» уже установлен, но его автор — <b>{old_author}</b>.\n'
                'Новый модуль написан автором <b>{new_author}</b>.\n\n'
                'Установка заблокирована во избежание перезаписи. Если хочешь заменить его, '
                'сначала удали старый: <code>{p}unload {name}</code>'
            ),
            'install_updating': '🔄 <b>Kaguya:</b> Обновление модуля «{name}» до v{version}...',
            'install_success_package': (
                '✅ <b>Модуль-пакет успешно установлен!</b>\n\n'
                '📦 <b>{name}</b> <code>v{version}</code>\n'
                ' ├ <i>{description}</i>\n'
                ' └ Папка модуля: <code>kaguya/modules/{module_name}</code>'
            ),
            'install_success_single': (
                '✅ <b>Модуль успешно установлен!</b>\n\n'
                '📦 <b>{name}</b> <code>v{version}</code>\n'
                ' ├ <i>{description}</i>\n'
                ' └ <b>Команды:</b> {cmds}'
            ),
            'install_damaged_syntax': '❌ <b>Kaguya:</b> Модуль поврежден:\n<code>{error}</code>',
            'install_failed': '❌ <b>Kaguya:</b> Не удалось загрузить модуль:\n<code>{error}</code>',

            'unload_usage': '❌ <b>Kaguya:</b> Укажи имя модуля. Пример: <code>.unload ИмяМодуля</code>',
            'unload_not_found': '❌ <b>Kaguya:</b> Модуль с именем «{target_name}» не найден.',
            'unload_core_protected': '❌ <b>Kaguya:</b> Нельзя удалять системные модули ядра.',
            'unload_success': '🗑 <b>Kaguya:</b> Модуль «{name}» успешно удален.',
            'unload_error': '❌ <b>Kaguya:</b> Ошибка при удалении модуля:\n<i>{error}</i>',

            'prefix_usage': (
                '⚙️ <b>Kaguya | Настройки префиксов</b>\n\n'
                '#️⃣ Текущие префиксы: {current}\n'
                ' └ Пример: <code>{p}prefix . !</code>'
            ),
            'prefix_invalid': '❌ <b>Kaguya:</b> Префикс должен состоять строго из одного символа!',
            'prefix_success': '✅ <b>Kaguya:</b> Префиксы команд успешно изменены на: {formatted}',

            'token_usage': (
                '⚙️ <b>Kaguya | Бот-ассистент</b>\n\n'
                'Для работы инлайн-функционала и кнопок тебе нужен свой бот.\n\n'
                '1. Зайди в @BotFather и создай бота\n'
                '2. В настройках бота включи <b>Inline Mode</b> (<b>ОБЯЗАТЕЛЬНО!</b>)\n'
                '3. В этом же меню поставь <b>Inline Feedback 100%</b>\n'
                '4. Скопируй токен и напиши: <code>{p}token твой_токен_бота</code>'
            ),
            'token_checking': '⏳ <b>Kaguya:</b> Проверяю токен...',
            'token_invalid': '❌ <b>Kaguya:</b> Неверный токен! Сверься с @BotFather.',
            'token_starting': '📥 <b>Kaguya:</b> Запуск ассистента...',
            'token_checking_inline': '⚙️ <b>Kaguya:</b> Проверяю инлайн-функционал...',
            'token_inline_disabled': (
                '⚠️ <b>Kaguya | Ошибка активации</b>\n\n'
                'Токен верный, но у твоего ассистента @{bot_username} <b>ВЫКЛЮЧЕН инлайн-режим</b>!\n\n'
                'Я прикрепила для тебя простую пошаговую инструкцию на картинке. '
                'Как только включишь, пришли токен заново через <code>{p}token твой_токен_бота</code>!\n\n'
                '🔗 BotFather: @BotFather'
            ),
            'token_api_error': '❌ <b>Kaguya:</b> Ошибка подключения к API Telegram: <code>{error}</code>',
            'token_rm_not_bound': '❌ <b>Kaguya:</b> Бот-ассистент и так не привязан.',
            'token_rm_stopping': '🗑 <b>Kaguya:</b> Остановка ассистента...',
            'token_rm_success': (
                '🗑 <b>Kaguya:</b> Бот-ассистент отвязан.\n\n'
                '<blockquote>Инлайн функционал выключен.</blockquote>'
            ),
            'inline_go_to_bot': '👾 Перейти к боту',
            'inline_setup_ok_title': 'Kaguya | Ассистент готов!',
            'inline_setup_ok_desc': 'Отправить подтверждение успешной настройки',
            'inline_setup_ok_text': (
                '🌸 <b>Kaguya | Бот-ассистент успешно привязан!</b>\n\n'
                '<blockquote>Все инлайн-функции и интерактивные кнопки активны и готовы к работе.</blockquote>'
            ),

            'lang_usage': (
                '⚙️ <b>Kaguya | Настройки языка</b>\n\n'
                '🌐 Текущий язык: <code>{current}</code>\n'
                ' ├ Доступные языки зависят от модулей (например, <code>ru</code>, <code>en</code>).\n'
                ' └ Изменить: <code>{p}lang en</code>'
            ),
            'lang_invalid': '❌ <b>Kaguya:</b> Код языка должен состоять строго из двух букв (например, <code>ru</code> или <code>en</code>)!',
            'lang_success': '✅ <b>Kaguya:</b> Язык системы успешно изменен на: <code>{new_lang}</code>'
        }
    }

    list_modules = list_modules
    install_module = install_module
    unload_module = unload_module
    set_token = set_token
    remove_token = remove_token
    system_inline = system_inline
    change_prefix = change_prefix
    assistant_start = assistant_start
    change_language = change_language
