"""
Конфигурация бота
"""
import os

# Токен бота (для PythonAnywhere берётся из переменных окружения)
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# URL для webhook
WEBHOOK_HOST = os.environ.get('WEBHOOK_HOST', 'https://YOUR_USERNAME.pythonanywhere.com')
WEBHOOK_PATH = f'/webhook/{BOT_TOKEN}'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

# База данных
DATABASE_PATH = 'student_bot.db'

# Администраторы (ваши Telegram ID)
ADMIN_IDS = [123456789]  # Замените на свой ID

# Часовой пояс
TIMEZONE = 'Europe/Moscow'

# Настройки для уведомлений
NOTIFICATION_HOUR = 9  # В какое время отправлять ежедневные уведомления (по UTC)
