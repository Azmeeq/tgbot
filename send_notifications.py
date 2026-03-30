"""
Скрипт для отправки ежедневных уведомлений
Запускается через Scheduled Tasks на PythonAnywhere
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
import logging

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aiogram import Bot
from config import BOT_TOKEN
from database import Database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def send_daily_notifications():
    """Отправить ежедневные уведомления о домашках"""

    bot = Bot(token=BOT_TOKEN)
    db = Database()

    try:
        logger.info("🔔 Начинаем отправку уведомлений...")

        # Получаем домашки на сегодня и завтра
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)

        today_str = today.strftime('%d.%m.%Y')
        tomorrow_str = tomorrow.strftime('%d.%m.%Y')

        # Получаем все группы
        db.cursor.execute('SELECT DISTINCT telegram_chat_id FROM groups')
        groups = db.cursor.fetchall()

        for group in groups:
            chat_id = group[0]

            # Получаем домашки группы
            homeworks = db.get_group_homework(chat_id, status='active')

            # Фильтруем по дедлайнам
            today_hw = []
            tomorrow_hw = []
            overdue_hw = []

            for hw in homeworks:
                deadline = hw['deadline']

                if today_str in deadline:
                    today_hw.append(hw)
                elif tomorrow_str in deadline:
                    tomorrow_hw.append(hw)
                elif self._is_overdue(deadline, today_str):
                    overdue_hw.append(hw)

            # Формируем сообщение
            if today_hw or tomorrow_hw or overdue_hw:
                message = "⏰ <b>Напоминание о домашках!</b>\n\n"

                if overdue_hw:
                    message += "❌ <b>ПРОСРОЧЕНО:</b>\n"
                    for hw in overdue_hw[:3]:
                        message += f"• {hw['subject']}: {hw['description']}\n"
                    message += "\n"

                if today_hw:
                    message += "🔴 <b>СЕГОДНЯ:</b>\n"
                    for hw in today_hw[:5]:
                        message += f"• {hw['subject']}: {hw['description']}\n"
                    message += "\n"

                if tomorrow_hw:
                    message += "🟡 <b>ЗАВТРА:</b>\n"
                    for hw in tomorrow_hw[:5]:
                        message += f"• {hw['subject']}: {hw['description']}\n"

                # Отправляем
                try:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode='HTML'
                    )
                    logger.info(f"✅ Уведомление отправлено в группу {chat_id}")

                    # Задержка, чтобы не превысить rate limit
                    await asyncio.sleep(0.5)

                except Exception as e:
                    logger.error(f"❌ Ошибка отправки в {chat_id}: {e}")

        logger.info("✅ Отправка уведомлений завершена")

    except Exception as e:
        logger.error(f"❌ Общая ошибка: {e}", exc_info=True)

    finally:
        await bot.session.close()
        db.close()

    def _is_overdue(self, deadline: str, today: str) -> bool:
        """Проверить, просрочен ли дедлайн"""
        try:
            # Простая проверка для форматов DD.MM.YYYY и DD.MM
            if len(deadline.split('.')) == 3:
                d_day, d_month, d_year = map(int, deadline.split('.'))
            elif len(deadline.split('.')) == 2:
                d_day, d_month = map(int, deadline.split('.'))
                d_year = datetime.now().year
            else:
                return False

            t_day, t_month, t_year = map(int, today.split('.'))

            deadline_date = datetime(d_year, d_month, d_day).date()
            today_date = datetime(t_year, t_month, t_day).date()

            return deadline_date < today_date

        except:
            return False


if __name__ == '__main__':
    asyncio.run(send_daily_notifications())