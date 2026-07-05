import logging
import os.path
import sys
import inspect
import importlib.util
import traceback
import html
from functools import wraps
from pathlib import Path
from pyrogram.handlers import MessageHandler, CallbackQueryHandler, InlineQueryHandler
from kaguya.client import KaguyaClient
from kaguya.types import BaseModule


logger = logging.getLogger('Kaguya.Loader')


def create_error_catcher(func):
    """Перехватчик исключений в модулях."""
    @wraps(func)
    async def wrapper(client, message, *args, **kwargs):
        try:
            return await func(client, message, *args, **kwargs)
        except Exception as e:
            logger.error(f'Ошибка выполнения запроса в модуле {e}', exc_info=True)

            tb_str = traceback.format_exc()
            if len(tb_str) > 3500:
                tb_str = tb_str[-3500:]

            tb_str = html.escape(tb_str)

            error_text = (
                f'❌ <b>Kaguya | Ошибка выполнения!</b>\n\n'
                f'<b>Исключение:</b> <code>{e}</code>\n\n'
                f'<b>Трассировка:</b>\n'
                f'<pre><code class="language-python">{tb_str}</code></pre>'
            )

            try:
                await message.edit_text(error_text)
            except Exception as edit_err:
                logger.warning(f'Не удалось отправить сообщение об ошибке: {edit_err}')
    return wrapper

class ModuleManager:
    def __init__(self, client: KaguyaClient):
        self.client = client

    def load_all_modules(self):
        """Загружает системные/пользовательские модули."""
        self._load_from_directory('kaguya/core_modules', 'kaguya.core_modules')
        self._load_from_directory('kaguya/modules', 'kaguya.modules')

    def _load_from_directory(self, directory: str, package_prefix: str):
        """Обходит модули. Поддерживает одиночные и пакетные модули."""
        if not os.path.exists(directory):
            os.makedirs(directory)
            return

        for item_name in os.listdir(directory):
            full_item_path = os.path.join(directory, item_name)

            if os.path.isfile(full_item_path) and item_name.endswith('.py') and item_name != '__init__.py':
                module_name = item_name[:-3]
                full_module_name = f'{package_prefix}.{module_name}'
                self._try_load_module(full_module_name, full_item_path, item_name, directory)

            elif os.path.isdir(full_item_path) and not item_name.startswith('.'):
                init_file_path = os.path.join(full_item_path, '__init__.py')
                if os.path.exists(init_file_path):
                    module_name = item_name
                    full_module_name = f'{package_prefix}.{module_name}'
                    self._try_load_module(full_module_name, init_file_path, item_name, directory)

    def _try_load_module(self, full_module_name: str, file_path: str, item_name: str, directory: str):
        """Вспомогательный метод для безопасной загрузки модуля."""
        try:
            self.load_module(full_module_name, file_path)
        except Exception as e:
            logger.error(f'Не удалось загрузить {item_name} из {directory}: {e}', exc_info=True)

    def load_module(self, module_name: str, file_path: str):
        """Загружает/перезагружает модуль."""
        if module_name in self.client.loaded_modules:
            self.client.unload_module_handler(module_name)
            self.client.loaded_modules.pop(module_name, None)
            sys.modules.pop(module_name, None)

        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f'Не удалось создать спецификацию для {file_path}')

        module_obj = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module_obj
        spec.loader.exec_module(module_obj)

        for _, obj in inspect.getmembers(module_obj):
            if inspect.isclass(obj) and issubclass(obj, BaseModule) and obj is not BaseModule:
                module_instance = obj(self.client)
                self.client.loaded_modules[module_name] = module_instance

                for _, method in inspect.getmembers(module_instance, predicate=inspect.ismethod):
                    if hasattr(method, '__kaguya_filter__'):
                        wrapped_method = create_error_catcher(method)
                        handler = MessageHandler(wrapped_method, getattr(method, '__kaguya_filter__'))
                        self.client.register_module_handler(module_name, handler)

                    if self.client.assistant:
                        if hasattr(method, '__kaguya_assistant_callback__'):
                            wrapped_method = create_error_catcher(method)
                            cb_filter = getattr(method, '__kaguya_assistant_callback__')
                            handler = CallbackQueryHandler(wrapped_method, cb_filter)
                            self.client.assistant.add_handler(handler)

                        if hasattr(method, '__kaguya_assistant_inline__'):
                            wrapped_method = create_error_catcher(method)
                            handler = InlineQueryHandler(wrapped_method)
                            self.client.assistant.add_handler(handler)

                        if hasattr(method, '__kaguya_assistant_command__'):
                            wrapped_method = create_error_catcher(method)
                            cmd_filter = getattr(method, '__kaguya_assistant_command__')
                            handler = MessageHandler(wrapped_method, cmd_filter)
                            self.client.assistant.add_handler(handler)

                logger.info(f'Модуль "{module_instance.meta.name}" ({module_name}) успешно загружен.')
                return module_instance.meta

        raise ValueError(f'В файле {file_path} не найден класс, унаследованный от BaseModule.')

    def register_assistant_handlers(self, assistant_client):
        """Регистрирует хэндлеры загруженных модулей на бота-ассистента."""
        for module_name, module_instance in self.client.loaded_modules.items():
            for _, method in inspect.getmembers(module_instance, predicate=inspect.ismethod):
                if hasattr(method, '__kaguya_assistant_callback__'):
                    wrapped_method = create_error_catcher(method)
                    cb_filter = getattr(method, '__kaguya_assistant_callback__')
                    handler = CallbackQueryHandler(wrapped_method, cb_filter)
                    assistant_client.add_handler(handler)

                if hasattr(method, '__kaguya_assistant_inline__'):
                    wrapped_method = create_error_catcher(method)
                    handler = InlineQueryHandler(wrapped_method)
                    assistant_client.add_handler(handler)

                if hasattr(method, '__kaguya_assistant_command__'):
                    wrapped_method = create_error_catcher(method)
                    cmd_filter = getattr(method, '__kaguya_assistant_command__')
                    handler = MessageHandler(wrapped_method, cmd_filter)
                    self.client.assistant.add_handler(handler)
