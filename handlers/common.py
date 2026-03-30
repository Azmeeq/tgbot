"""
Общие команды бота
"""
from aiogram import Router, types
from aiogram.filters import Command
from database import Database

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message, db: Database):
    """Приветствие"""

    # Сохраняем пользователя в БД
    db.add_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )

    if message.chat.type == 'private':
        await message.answer(
            "👋 Привет! Я бот для управления домашними заданиями.\n\n"
            
            "<b>📚 В групповом чате:</b>\n"
            "/add_hw - добавить домашку\n"
            "/homework - показать все домашки\n"
            "/homework [предмет] - домашки по предмету\n"
            "/delete_hw [номер] - удалить домашку\n"
            "/done_hw [номер] - отметить выполненной\n"
            "/stats - статистика группы\n\n"
            
            "<b>🔒 В личных сообщениях:</b>\n"
            "/add_task - добавить личную задачу\n"
            "/my_tasks - мои задачи\n"
            "/done_task [номер] - отметить выполненной\n\n"
            
            "<b>📖 Помощь:</b>\n"
            "/help - подробная справка\n\n"
            
            "Добавь меня в групповой чат твоей учебной группы!",
            parse_mode='HTML'
        )
    else:
        # В группе - короткое сообщение
        await message.answer(
            "👋 Привет! Я готов помогать с домашками!\n"
            "Используй /help для списка команд",
            parse_mode='HTML'
        )


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Справка"""

    help_text = (
        "📖 <b>Подробная справка</b>\n\n"
        
        "<b>ДОМАШНИЕ ЗАДАНИЯ (в группе):</b>\n\n"
        
        "<code>/add_hw Предмет | Описание | Дедлайн</code>\n"
        "Добавить домашку\n"
        "Пример: /add_hw Математика | Задачи 1-10 стр.45 | 25.01.2024\n\n"
        
        "<code>/homework</code>\n"
        "Показать все активные домашки\n\n"
        
        "<code>/homework Математика</code>\n"
        "Показать домашки по предмету\n\n"
        
        "<code>/delete_hw 5</code>\n"
        "Удалить домашку #5 (может только тот, кто добавил, или админ)\n\n"
        
        "<code>/done_hw 5</code>\n"
        "Отметить домашку #5 как выполненную\n\n"
        
        "<code>/stats</code>\n"
        "Статистика группы\n\n"
        
        "<b>ЛИЧНЫЕ ЗАДАЧИ (в личке):</b>\n\n"
        
        "<code>/add_task</code>\n"
        "Добавить личную задачу (интерактивно)\n\n"
        
        "<code>/my_tasks</code>\n"
        "Показать мои задачи\n\n"
        
        "<code>/done_task 3</code>\n"
        "Отметить задачу #3 как выполненную\n\n"
        
        "❓ Вопросы? Напиши @your_username"
    )

    await message.answer(help_text, parse_mode='HTML')