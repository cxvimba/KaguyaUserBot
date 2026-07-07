from kaguya.types import BaseModule, ModuleInfo
from .modules import list_modules, install_module, unload_module
from .token import set_token, remove_token, system_inline
from .prefix import change_prefix
from .assistant import assistant_start


class SystemModule(BaseModule):
    meta = ModuleInfo(
        name='Система',
        description='Встроенные системные команды для Kaguya',
        version='1.0.1',
        author='cxvimba',
        commands={
            'modules | модули': 'Показать список всех активных модулей',
            'install | установить': 'Установить модуль (ответом на .py, .txt или .zip)',
            'unload | удалить': 'Выгрузить модуль из памяти (.unload Модуль)',
            'prefix | префикс': 'Изменить префиксы команд (.prefix . !)',
            'token | токен': 'Привязать бота-ассистента для инлайн-кнопок',
            'token_rm | токен_удалить': 'Отвязать бота-ассистента'
        }
    )

    list_modules = list_modules
    install_module = install_module
    unload_module = unload_module

    set_token = set_token
    remove_token = remove_token
    system_inline = system_inline

    change_prefix = change_prefix

    assistant_start = assistant_start
