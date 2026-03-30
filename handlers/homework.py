"""
Обработчики для домашних заданий
"""
from aiogram import Router, types, F
from aiogram.filters import Command
from database import Database
from utils import parse_deadline, format_homework_list
import logging

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("add_hw"))
async def add_homework(message: types.Message, db: Database):
    """Добавить домашку"""

    # Только в группе
    if message.chat.type == 'private':
        await message.reply(
            "❌ Эта команда работает только в групповом чате!\n"
            "Добавь меня в группу и попробуй там."
        )
        return

    try:
        # Сохраняем группу
        db.add_group(
            telegram_chat_id=message.chat.id,
            name=message.chat.title
        )

        # Сохраняем пользователя
        user_id = db.add_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name
        )

        # Парсим сообщение
        text = message.text.replace('/add_hw', '').strip()

        if not text:
            await message.reply(
                "❌ <b>Формат:</b>\n"
                "<code>/add_hw Предмет | Описание | Дедлайн</code>\n\n"
                
                "<b>Примеры:</b>\n"
                "<code>/add_hw Математика | Задачи 1-10 стр.45 | 25.01.2024</code>\n"
                "<code>/add_hw Физика | Лабораторная №3 | завтра</code>\n"
                "<code>/add_hw Программирование | Проект | 30.01</code>\n\n"
                
                "<b>Дедлайн можно указать:</b>\n"
                "• 25.01.2024\n"
                "• 25.01\n"
                "• завтра\n"
                "• послезавтра",
                parse_mode='HTML'
            )
            return

        parts = text.split('|')

        if len(parts) < 3:
            await message.reply(
                "❌ Не хватает данных!\n\n"
                "Нужно указать: <b>Предмет</b> | <b>Описание</b> | <b>Дедлайн</b>",
                parse_mode='HTML'
            )
            return

        subject = parts[0].strip()
        description = parts[1].strip()
        deadline_raw = parts[2].strip()

        # Парсим дедлайн
        deadline = parse_deadline(deadline_raw)

        # Определяем приоритет по ключевым словам
        priority = 'medium'
        description_lower = description.lower()

        if any(word in description_lower for word in ['срочно', 'важно', 'экзамен', 'контрольная']):
            priority = 'high'
        elif any(word in description_lower for word in ['опционально', 'по желанию']):
            priority = 'low'

        # Сохраняем
        hw_id = db.add_homework(
            user_id=user_id,
            username=message.from_user.full_name or message.from_user.username or 'Аноним',
            group_id=message.chat.id,
            subject=subject,
            description=description,
            deadline=deadline,
            priority=priority
        )

        priority_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}

        await message.reply(
            f"✅ Домашка <b>#{hw_id}</b> добавлена!\n\n"
            f"{priority_emoji[priority]} <b>{subject}</b>\n"
            f"📝 {description}\n"
            f"📅 До: {deadline}\n"
            f"👤 Добавил: {message.from_user.full_name}",
            parse_mode='HTML'
        )

    except Exception as e:
        logger.error(f"Error in add_homework: {e}", exc_info=True)
        await message.reply(f"❌ Ошибка: {str(e)}")


@router.message(Command("homework"))
async def show_homework(message: types.Message, db: Database):
    """Показать домашки"""

    if message.chat.type == 'private':
        await message.reply(
            "❌ Эта команда работает только в групповом чате!\n"
            "Для личных задач используй /my_tasks"
        )
        return

    try:
        # Проверяем, есть ли фильтр по предмету
        text = message.text.replace('/homework', '').strip()

        if text:
            # Фильтр по предмету
            homeworks = db.get_homework_by_subject(message.chat.id, text)

            if not homeworks:
                await message.reply(
                    f"📭 Домашек по предмету <b>'{text}'</b> не найдено",
                    parse_mode='HTML'
                )
                return

            formatted = format_homework_list(homeworks)
            await message.reply(formatted, parse_mode='HTML')
        else:
            # Все домашки
            homeworks = db.get_group_homework(message.chat.id)

            if not homeworks:
                await message.reply("🎉 Домашек нет! Отдыхаем!")
                return

            formatted = format_homework_list(homeworks)
            await message.reply(formatted, parse_mode='HTML')

    except Exception as e:
        logger.error(f"Error in show_homework: {e}", exc_info=True)
        await message.reply(f"❌ Ошибка: {str(e)}")


@router.message(Command("delete_hw"))
async def delete_homework(message: types.Message, db: Database):
    """Удалить домашку"""

    if message.chat.type == 'private':
        await message.reply("❌ Команда работает только в групповом чате!")
        return

    try:
        # Парсим номер
        text = message.text.replace('/delete_hw', '').strip()

        if not text.isdigit():
            await message.reply(
                "❌ Укажите номер домашки\n\n"
                "Пример: <code>/delete_hw 5</code>",
                parse_mode='HTML'
            )
            return

        hw_id = int(text)

        # Получаем домашку
        hw = db.get_homework_by_id(hw_id)

        if not hw:
            await message.reply(f"❌ Домашка #{hw_id} не найдена")
            return

        # Проверяем права (может удалить только автор или админ)
        user = db.get_user_by_telegram_id(message.from_user.id)

        if hw['user_id'] != user['id']:
            # Проверяем, админ ли
            chat_member = await message.bot.get_chat_member(
                message.chat.id,
                message.from_user.id
            )

            if chat_member.status not in ['creator', 'administrator']:
                await message.reply(
                    "❌ Удалить домашку может только тот, кто её добавил, "
                    "или администратор группы"
                )
                return

        # Удаляем
        db.delete_homework(hw_id)

        await message.reply(
            f"✅ Домашка <b>#{hw_id}</b> удалена\n\n"
            f"<s>{hw['subject']} - {hw['description']}</s>",
            parse_mode='HTML'
        )

    except ValueError:
        await message.reply("❌ Неверный номер домашки")
    except Exception as e:
        logger.error(f"Error in delete_homework: {e}", exc_info=True)
        await message.reply(f"❌ Ошибка: {str(e)}")


@router.message(Command("done_hw"))
async def mark_homework_done(message: types.Message, db: Database):
    """Отметить домашку как выполненную"""

    if message.chat.type == 'private':
        await message.reply("❌ Команда работает только в групповом чате!")
        return

    try:
        text = message.text.replace('/done_hw', '').strip()

        if not text.isdigit():
            await message.reply(
                "❌ Укажите номер домашки\n\n"
                "Пример: <code>/done_hw 5</code>",
                parse_mode='HTML'
            )
            return

        hw_id = int(text)

        # Получаем домашку
        hw = db.get_homework_by_id(hw_id)

        if not hw:
            await message.reply(f"❌ Домашка #{hw_id} не найдена")
            return

        if hw['status'] == 'completed':
            await message.reply(f"✅ Домашка #{hw_id} уже отмечена как выполненная")
            return

        # Отмечаем
        db.mark_homework_done(hw_id)

        await message.reply(
            f"✅ Домашка <b>#{hw_id}</b> отмечена как выполненная!\n\n"
            f"🎉 {hw['subject']} - {hw['description']}",
            parse_mode='HTML'
        )

    except ValueError:
        await message.reply("❌ Неверный номер домашки")
    except Exception as e:
        logger.error(f"Error in mark_homework_done: {e}", exc_info=True)
        await message.reply(f"❌ Ошибка: {str(e)}")


@router.message(Command("stats"))
async def show_stats(message: types.Message, db: Database):
    """Статистика группы"""

    if message.chat.type == 'private':
        await message.reply("❌ Команда работает только в групповом чате!")
        return

    try:
        stats = db.get_group_stats(message.chat.id)

        text = (
            "📊 <b>Статистика группы</b>\n\n"
            f"📚 Всего домашек: {stats['total']}\n"
            f"✅ Выполнено: {stats['completed']}\n"
            f"📋 Активных: {stats['active']}\n"
        )

        if stats['total'] > 0:
            completion_rate = (stats['completed'] / stats['total']) * 100
            text += f"📈 Процент выполнения: {completion_rate:.1f}%\n"

        if stats['top_user']:
            text += f"\n🏆 Самый активный: {stats['top_user']['username']} ({stats['top_user']['count']} домашек)"

        await message.reply(text, parse_mode='HTML')

    except Exception as e:
        logger.error(f"Error in show_stats: {e}", exc_info=True)
        await message.reply(f"❌ Ошибка: {str(e)}")