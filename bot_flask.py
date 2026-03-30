"""
Flask-версия бота для PythonAnywhere
"""
import os
import logging
from flask import Flask, request, jsonify
from aiogram import Bot, Dispatcher, types
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
import asyncio

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_HOST = os.environ.get('WEBHOOK_HOST')
WEBHOOK_PATH = f'/webhook/{BOT_TOKEN}'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

# Создаём Flask приложение
app = Flask(__name__)

# Создаём бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Импортируем обработчики
from database import Database
from handlers import common, homework, personal

# База данных
db = Database()

# Middleware для передачи db
@dp.message.middleware()
async def db_middleware(handler, event, data):
    data['db'] = db
    return await handler(event, data)

# Регистрируем роутеры
dp.include_router(common.router)
dp.include_router(homework.router)
dp.include_router(personal.router)


# ==================== FLASK ROUTES ====================

@app.route('/')
def index():
    return 'Bot is running!'


@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'webhook_url': WEBHOOK_URL
    })


@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    """Обработка webhook от Telegram"""
    try:
        # Получаем update от Telegram
        update_dict = request.get_json(force=True)
        
        # Создаём Update объект
        update = types.Update(**update_dict)
        
        # ✅ ИСПРАВЛЕНО: Используем новый event loop правильно
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(dp.feed_update(bot, update))
        finally:
            loop.close()
        
        return 'OK', 200
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return 'Error', 500


@app.route('/set_webhook')
def set_webhook():
    """Установка webhook (вызывается один раз)"""
    try:
        asyncio.run(_set_webhook())
        return jsonify({
            'status': 'ok',
            'webhook_url': WEBHOOK_URL
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


async def _set_webhook():
    """Установить webhook"""
    await bot.set_webhook(
        url=WEBHOOK_URL,
        drop_pending_updates=True
    )
    logger.info(f"Webhook set to {WEBHOOK_URL}")


# ==================== ЗАПУСК ====================

if __name__ == '__main__':
    # Локальный запуск для тестирования
    app.run(host='0.0.0.0', port=8000, debug=True)
