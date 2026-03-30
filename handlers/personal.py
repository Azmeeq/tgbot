"""
Обработчики для личных задач
"""
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import Database
from utils import format_personal_tasks
import logging

router = Router()
logger = logging.getLogger(__name__)


class AddTaskStates(StatesGroup):
    """Состояния для добавления задачи"""
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_deadline = State()


@router.message(Command("add_task"))
async def start_add_task(message: types.Message, state: FSMContext, db: Database):
    """Начать добавление личной задачи"""

    if message.chat.type != 'private':
        await message.reply(
            "❌ Личные задачи добавляются только в личных сообщениях!\n"
            "Напиши мне в ЛС: @your_bot_username"
        )
        return

    # Сохраняем пользователя
    db.add_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )

    await state.set_state(AddTaskStates.waiting_for_title)
    await message.answer(
        "📝 <b>Новая задача</b>\n\n"
        "Введите название задачи:",
        parse_mode='HTML'
    )


@router.message(AddTaskStates.waiting_for_title)
async def process_title(message: types.Message, state: FSMContext):
    """Обработка названия задачи"""

    await state.update_data(title=message.text)
    await state.set_state(AddTaskStates.waiting_for_description)

    await message.answer(
        "📋 Введите описание задачи\n"
        "(или отправьте '-' чтобы пропустить):"
    )


@router.message(AddTaskStates.waiting_for_description)
async def process_description(message: types.Message, state: FSMContext):
    """Обработка описания"""

    description = None if message.text == '-' else message.text
    await state.update_data(description=description)
    await state.set_state(AddTaskStates.waiting_for_deadline)

    await message.answer(
        "📅 Введите дедлайн\n"
        "(или отправьте '-' чтобы пропустить)\n\n"
        "Примеры:\n"
        "• 25.01.2024\n"
        "• 25.01\n"
        "• завтра\n"
        "• послезавтра"
    )


@router.message(AddTaskStates.waiting_for_deadline)
async def process_deadline(message: types.Message, state: FSMContext, db: Database):
    """Обработка дедлайна и сохранение задачи"""

    from utils import parse_deadline

    deadline = None if message.text == '-' else parse_deadline(message.text)

    # Получаем все данные
    data = await state.get_data()

    # Сохраняем задачу
    user = db.get_user_by_telegram_id(message.from_user.id)

    task_id = db.add_personal_task(
        user_id=user['id'],
        title=data['title'],
        description=data.get('description'),
        deadline=deadline
    )

    # Очищаем состояние
    await state.clear()

    # Отправляем подтверждение
    text = (
        f"✅ Задача <b>#{task_id}</b> добавлена!\n\n"
        f"📌 {data['title']}\n"
    )

    if data.get('description'):
        text += f"📝 {data['description']}\n"

    if deadline:
        text += f"📅 До: {deadline}\n"

    await message.answer(text, parse_mode='HTML')


@router.message(Command("my_tasks"))
async def show_my_tasks(message: types.Message, db: Database):
    """Показать мои задачи"""

    if message.chat.type != 'private':
        await message.reply("❌ Команда работает только в личных сообщениях!")
        return

    try:
        user = db.get_user_by_telegram_id(message.from_user.id)

        if not user:
            await message.answer("❌ Вы не зарегистрированы. Используйте /start")
            return

        tasks = db.get_personal_tasks(user['id'])

        if not tasks:
            await message.answer(
                "📭 У вас нет активных задач\n\n"
                "Добавьте новую: /add_task"
            )
            return

        formatted = format_personal_tasks(tasks)
        await message.answer(formatted, parse_mode='HTML')

    except Exception as e:
        logger.error(f"Error in show_my_tasks: {e}", exc_info=True)
        await message.reply(f"❌ Ошибка: {str(e)}")


@router.message(Command("done_task"))
async def mark_task_done(message: types.Message, db: Database):
    """Отметить задачу как выполненную"""

    if message.chat.type != 'private':
        await message.reply("❌ Команда работает только в личных сообщениях!")
        return

    try:
        text = message.text.replace('/done_task', '').strip()

        if not text.isdigit():
            await message.reply(
                "❌ Укажите номер задачи\n\n"
                "Пример: <code>/done_task 3</code>",
                parse_mode='HTML'
            )
            return

        task_id = int(text)

        # Отмечаем
        db.mark_personal_task_done(task_id)

        await message.reply(
            f"✅ Задача <b>#{task_id}</b> выполнена! 🎉",
            parse_mode='HTML'
        )

    except ValueError:
        await message.reply("❌ Неверный номер задачи")
    except Exception as e:
        logger.error(f"Error in mark_task_done: {e}", exc_info=True)
        await message.reply(f"❌ Ошибка: {str(e)}")