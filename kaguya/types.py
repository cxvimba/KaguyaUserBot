from dataclasses import dataclass, field
from typing import Dict, Callable, Optional
from pyrogram import Client, filters
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

    def __init__(self, client: Client):
        self.client = client


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


def on_assistant_inline():
    """Обработчик Inline-запросов бота-ассистента."""
    def decorator(func_cb):
        func_cb.__kaguya_assistant_inline__ = True
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
