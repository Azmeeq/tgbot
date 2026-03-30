"""
Вспомогательные функции
"""
from datetime import datetime
import re


def parse_deadline(text: str) -> str:
    """
    Парсинг дедлайна из текста
    Поддерживает форматы:
    - 25.01.2024
    - 25.01
    - завтра
    - послезавтра
    """
    text = text.strip().lower()

    # Простые форматы дат
    if re.match(r'\d{2}\.\d{2}\.\d{4}', text):
        return text

    if re.match(r'\d{2}\.\d{2}', text):
        year = datetime.now().year
        return f"{text}.{year}"

    # Относительные даты
    from datetime import timedelta

    if text == 'завтра':
        date = datetime.now() + timedelta(days=1)
        return date.strftime('%d.%m.%Y')

    if text == 'послезавтра':
        date = datetime.now() + timedelta(days=2)
        return date.strftime('%d.%m.%Y')

    # Если не распознано, возвращаем как есть
    return text


def format_homework_list(homeworks: list, max_items: int = 10) -> str:
    """Форматировать список домашек"""
    if not homeworks:
        return "📭 Домашек нет! Отдыхаем! 🎉"

    text = "📚 <b>Актуальные домашки:</b>\n\n"

    priority_emoji = {
        'high': '🔴',
        'medium': '🟡',
        'low': '🟢'
    }

    for i, hw in enumerate(homeworks[:max_items], 1):
        emoji = priority_emoji.get(hw['priority'], '⚪')

        text += (
            f"{emoji} <b>#{hw['id']} {hw['subject']}</b>\n"
            f"📝 {hw['description']}\n"
            f"📅 До: {hw['deadline']}\n"
            f"👤 {hw['username']}\n"
        )

        if i < len(homeworks[:max_items]):
            text += f"{'─' * 30}\n\n"

    if len(homeworks) > max_items:
        text += f"\n<i>...и ещё {len(homeworks) - max_items} домашек</i>"

    return text


def format_personal_tasks(tasks: list) -> str:
    """Форматировать список личных задач"""
    if not tasks:
        return "📭 У вас нет активных задач"

    text = "📋 <b>Ваши задачи:</b>\n\n"

    priority_emoji = {
        'high': '🔴',
        'medium': '🟡',
        'low': '🟢'
    }

    for task in tasks:
        emoji = priority_emoji.get(task['priority'], '⚪')

        text += f"{emoji} <b>{task['title']}</b>\n"

        if task['description']:
            text += f"   {task['description']}\n"

        if task['deadline']:
            text += f"   📅 До: {task['deadline']}\n"

        text += "\n"

    return text


def is_admin(user_id: int, admin_ids: list) -> bool:
    """Проверка, является ли пользователь администратором"""
    return user_id in admin_ids