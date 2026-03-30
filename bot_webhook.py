"""
Основной файл бота для работы через webhook на PythonAnywhere
"""
import os
import sys
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Импорты
from config import BOT_TOKEN, WEBHOOK_PATH, WEBHOOK_URL
from database import Database
from handlers import common, homework, personal

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Инициализация
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# База данных (глобальный экземпляр)
db = Database()


# ==================== MIDDLEWARE ====================

@dp.message.middleware()
async def db_middleware(handler, event, data):
    """Middleware для передачи db в хендлеры"""
    data['db'] = db
    return await handler(event, data)


@dp.callback_query.middleware()
async def db_middleware_callback(handler, event, data):
    """Middleware для callback query"""
    data['db'] = db
    return await handler(event, data)


# ==================== РЕГИСТРАЦИЯ РОУТЕРОВ ====================

dp.include_router(common.router)
dp.include_router(homework.router)
dp.include_router(personal.router)


# ==================== WEBHOOK HANDLERS ====================

async def on_startup(app):
    """При запуске устанавливаем webhook"""
    try:
        webhook_info = await bot.get_webhook_info()

        if webhook_info.url != WEBHOOK_URL:
            await bot.set_webhook(
                url=WEBHOOK_URL,
                drop_pending_updates=True
            )
            logger.info(f"✅ Webhook установлен: {WEBHOOK_URL}")
        else:
            logger.info(f"✅ Webhook уже установлен: {WEBHOOK_URL}")

    except Exception as e:
        logger.error(f"❌ Ошибка установки webhook: {e}", exc_info=True)


async def on_shutdown(app):
    """При остановке удаляем webhook"""
    try:
        await bot.delete_webhook()
        await bot.session.close()
        db.close()
        logger.info("✅ Webhook удалён, соединения закрыты")
    except Exception as e:
        logger.error(f"❌ Ошибка при shutdown: {e}", exc_info=True)


# ==================== HEALTH CHECK ====================

async def health_check(request):
    """Эндпоинт для проверки здоровья бота"""
    try:
        # Проверяем БД
        db.cursor.execute('SELECT 1')

        # Проверяем webhook
        webhook_info = await bot.get_webhook_info()

        status = {
            'status': 'ok',
            'webhook_url': webhook_info.url,
            'pending_updates': webhook_info.pending_update_count
        }

        return web.json_response(status)

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return web.json_response(
            {'status': 'error', 'message': str(e)},
            status=500
        )


# ==================== ГЛАВНАЯ ФУНКЦИЯ ====================

def create_app():
    """Создать и настроить aiohttp приложение"""

    # Создаём приложение
    app = web.Application()

    # Регистрируем startup/shutdown
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Health check endpoint
    app.router.add_get('/health', health_check)
    app.router.add_get('/', lambda r: web.Response(text="Bot is running!"))

    # Настраиваем webhook handler
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )

    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    # Настраиваем приложение
    setup_application(app, dp, bot=bot)

    logger.info("✅ Приложение создано и настроено")

    return app


# ==================== WSGI APPLICATION ====================

# Для PythonAnywhere
application = create_app()


# ==================== ЛОКАЛЬНЫЙ ЗАПУСК ====================

if __name__ == '__main__':
    """Для локального тестирования"""

    logger.info("🚀 Запуск бота в режиме разработки...")
    logger.info(f"📡 Webhook URL: {WEBHOOK_URL}")

    web.run_app(
        application,
        host='0.0.0.0',
        port=8000
    )