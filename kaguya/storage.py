import asyncio
import logging
import os.path
import shutil
from typing import Any, Optional
from diskcache import Cache


logger = logging.getLogger('Kaguya.Storage')

class AsyncCache:
    """Асинхронное хранилище."""
    def __init__(self, directory: str):
        self.directory = directory
        self._cache = Cache(directory)

    async def get(self, key: Any, default: Any = None) -> Any:
        """Получает значение ключа."""
        return await asyncio.to_thread(self._cache.get, key, default=default)

    async def set(self, key: Any, value: Any, expire: Optional[float] = None) -> bool:
        """Записывает значение."""
        return await asyncio.to_thread(self._cache.set, key, value, expire=expire)

    async def delete(self, key: Any) -> bool:
        """Удаляет ключ."""
        return await asyncio.to_thread(self._cache.delete, key)

    async def clear(self):
        """Очищает текущую директорию."""
        await asyncio.to_thread(self._cache.clear)

    async def close(self):
        """Закрывает соединение с хранилищем."""
        await asyncio.to_thread(self._cache.close)


class KaguyaStorage:
    """Менеджер категорий хранилища."""
    def __init__(self, base_dir: str = 'data/storage'):
        self.base_dir = base_dir
        self._active_caches: dict[str, AsyncCache] = {}

    def get_category(self, category_name: str) -> AsyncCache:
        """Возвращает изолированную категорию хранилища."""
        safe_name = ''.join(c for c in category_name if c.isalnum() or c in ('_', '-'))
        if not safe_name:
            raise ValueError(f'Недопустимое имя категории: {category_name}')

        if safe_name not in self._active_caches:
            dir_path = os.path.join(self.base_dir, safe_name)
            self._active_caches[safe_name] = AsyncCache(dir_path)
            logger.debug(f'Инициирована категория кэша: {safe_name} ({dir_path})')

        return self._active_caches[safe_name]

    async def delete_category(self, category_name: str) -> bool:
        """Удаляет категорию из хранилища."""
        safe_name = ''.join(c for c in category_name if c.isalnum() or c in ('_', '-'))
        if safe_name in self._active_caches:
            await self._active_caches[safe_name].close()
            self._active_caches.pop(safe_name)

        dir_path = os.path.join(self.base_dir, safe_name)
        if os.path.exists(dir_path):
            await asyncio.to_thread(shutil.rmtree, dir_path)
            logger.info(f'Категория {safe_name} полностью удалена с диска.')
            return True
        return False

    async def close_all(self):
        """Закрывает все открытые соединения кэша."""
        for cache in self._active_caches.values():
            await cache.close()
        self._active_caches.clear()
