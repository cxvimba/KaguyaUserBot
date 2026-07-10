from dataclasses import dataclass, field
from typing import Dict, Callable, Optional
from pyrogram import filters, Client
from pyrogram.filters import Filter
from pyrogram.types import Message


@dataclass(frozen=True)
class ModuleInfo:
    """Метаданные модуля."""
    name: str
    """Название модуля."""
    description: str
    """Описание модуля."""
    version: str = '1.0.0'
    """Версия модуля."""
    author: str = 'Anonymous'
    """Автор модуля."""
    commands: Dict[str, str] = field(default_factory=dict)
    """Команды модуля: [Command, "Описание команды"]."""


class BaseModule:
    """Базовый класс для всех модулей."""
    meta: ModuleInfo
    LANGUAGES: dict = {}

    def __init__(self, client: Client):
        self.client = client

    def get_text(self, key: str) -> str:
        """
        Возвращает локализированный текст по ключу.
        Если текущего языка системы нет в LANGUAGES — возвращает значение первого языка в списке локализации модуля.
        """
        if not self.LANGUAGES:
            return f'[{key}]'

        lang = self.client.get_lang()

        if lang in self.LANGUAGES and key in self.LANGUAGES[lang]:
            return self.LANGUAGES[lang][key]

        first_lang = list(self.LANGUAGES.keys())[0]
        if key in self.LANGUAGES[first_lang]:
            return self.LANGUAGES[first_lang][key]

        return f'[{key}]'


def on_event(custom_filter: Filter):
    """Декоратор для привязки к событиям."""
    def decorator(func: Callable):
        func.__kaguya_filter__ = custom_filter
        return func
    return decorator


def on_command(command_name: str):
    """
    Декоратор для обработки личных команды.
    Поддерживает динамический префикс команд и алиасы.
    """
    if isinstance(command_name, str):
        commands = [command_name.lower()]
    else:
        commands = [cmd.lower() for cmd in command_name]

    async def func(_, client, message: Message):
        is_me = bool(message.from_user and message.from_user.is_self or message.outgoing)
        if not is_me:
            return False

        if not message.text and not message.caption:
            return False

        prefixes = getattr(client, 'prefixes', ['.', '/'])
        text = message.text or message.caption
        parts = text.split()
        if not parts:
            return False

        trigger = parts[0].lower()
        for cmd in commands:
            for p in prefixes:
                if trigger == f'{p}{cmd}':
                    message.command = [cmd] + parts[1:]
                    return True
        return False

    cmd_filter = filters.create(func)
    return on_event(cmd_filter)


def on_assistant_callback(pattern: Optional[str] = None):
    """Обработчик callback вызовов бота-ассистента."""
    if pattern:
        async def func(_, __, cb):
            return bool(cb.data and cb.data.startswith(pattern))
        custom_filter = filters.create(func)
    else:
        custom_filter = None

    def decorator(func_cb):
        func_cb.__kaguya_assistant_callback__ = custom_filter
        return func_cb
    return decorator


def on_assistant_inline(pattern: str | None = None):
    """Обработчик Inline-запросов бота-ассистента."""
    if pattern:
        async def func(_, __, inline_query):
            return bool(inline_query.query and inline_query.query.startswith(pattern))

        custom_filter = filters.create(func)
    else:
        custom_filter = None

    def decorator(func_cb):
        func_cb.__kaguya_assistant_inline__ = custom_filter
        return func_cb

    return decorator


def on_assistant_command(command_name: str | list[str]):
    """Обработчик команд бота-ассистента."""
    commands = [command_name] if isinstance(command_name, str) else list(command_name)
    cmd_filter = filters.command(commands, prefixes='/')

    def decorator(func_cb):
        func_cb.__kaguya_assistant_command__ = cmd_filter
        return func_cb
    return decorator


def on_fsm(state: str):
    """Обработчик сообщений в определенном состоянии FSM."""
    async def func(_, client, message: Message):
        if not message.text and not message.caption:
            return False

        settings = client.db.get_category('settings')
        current_state = await settings.get('fsm_state')
        return current_state == state

    fsm_filter = filters.create(func)
    return on_event(fsm_filter)
