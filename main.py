import asyncio
import logging
from kaguya.client import KaguyaClient


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Kaguya.Main')


async def main():
    bot = KaguyaClient()
    await bot.start_kaguya()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Kaguya остановлена пользователем.')
