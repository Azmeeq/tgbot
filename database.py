"""
Работа с базой данных
"""
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path='student_bot.db'):
        self.db_path = db_path
        self.connection = sqlite3.connect(
            db_path,
            check_same_thread=False,
            timeout=10.0
        )
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        self._create_tables()
        logger.info(f"Database initialized: {db_path}")

    def _create_tables(self):
        """Создать все необходимые таблицы"""

        # Таблица пользователей
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица групп
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_chat_id INTEGER UNIQUE NOT NULL,
                name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица участников групп
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_members (
                group_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT DEFAULT 'member',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (group_id, user_id),
                FOREIGN KEY (group_id) REFERENCES groups(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # Таблица домашних заданий
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS homework (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                group_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                description TEXT NOT NULL,
                deadline TEXT NOT NULL,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (group_id) REFERENCES groups(id)
            )
        ''')

        # Таблица личных задач
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS personal_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                deadline TEXT,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # Индексы для оптимизации
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_homework_group 
            ON homework(group_id, status)
        ''')

        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_homework_deadline 
            ON homework(deadline)
        ''')

        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_personal_user 
            ON personal_tasks(user_id, status)
        ''')

        self.connection.commit()
        logger.info("Database tables created/verified")

    # ==================== USERS ====================

    def add_user(self, telegram_id: int, username: str = None, full_name: str = None) -> int:
        """Добавить или обновить пользователя"""
        try:
            self.cursor.execute('''
                INSERT INTO users (telegram_id, username, full_name)
                VALUES (?, ?, ?)
                ON CONFLICT(telegram_id) DO UPDATE SET
                    username = excluded.username,
                    full_name = excluded.full_name
            ''', (telegram_id, username, full_name))

            self.connection.commit()

            # Получаем ID пользователя
            self.cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
            return self.cursor.fetchone()[0]

        except Exception as e:
            logger.error(f"Error adding user: {e}")
            raise

    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict]:
        """Получить пользователя по Telegram ID"""
        self.cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    # ==================== GROUPS ====================

    def add_group(self, telegram_chat_id: int, name: str = None) -> int:
        """Добавить группу"""
        try:
            self.cursor.execute('''
                INSERT INTO groups (telegram_chat_id, name)
                VALUES (?, ?)
                ON CONFLICT(telegram_chat_id) DO UPDATE SET
                    name = excluded.name
            ''', (telegram_chat_id, name))

            self.connection.commit()

            self.cursor.execute('SELECT id FROM groups WHERE telegram_chat_id = ?', (telegram_chat_id,))
            return self.cursor.fetchone()[0]

        except Exception as e:
            logger.error(f"Error adding group: {e}")
            raise

    def add_group_member(self, group_id: int, user_id: int, role: str = 'member'):
        """Добавить участника в группу"""
        try:
            self.cursor.execute('''
                INSERT INTO group_members (group_id, user_id, role)
                VALUES (?, ?, ?)
                ON CONFLICT(group_id, user_id) DO UPDATE SET
                    role = excluded.role
            ''', (group_id, user_id, role))

            self.connection.commit()

        except Exception as e:
            logger.error(f"Error adding group member: {e}")
            raise

    # ==================== HOMEWORK ====================

    def add_homework(
            self,
            user_id: int,
            username: str,
            group_id: int,
            subject: str,
            description: str,
            deadline: str,
            priority: str = 'medium'
    ) -> int:
        """Добавить домашку"""
        try:
            self.cursor.execute('''
                INSERT INTO homework (user_id, username, group_id, subject, description, deadline, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, username, group_id, subject, description, deadline, priority))

            self.connection.commit()
            hw_id = self.cursor.lastrowid

            logger.info(f"Homework added: ID={hw_id}, subject={subject}, group={group_id}")
            return hw_id

        except Exception as e:
            logger.error(f"Error adding homework: {e}")
            raise

    def get_group_homework(self, group_id: int, status: str = 'active') -> List[Dict]:
        """Получить домашки группы"""
        try:
            query = '''
                SELECT * FROM homework 
                WHERE group_id = ?
            '''
            params = [group_id]

            if status:
                query += ' AND status = ?'
                params.append(status)

            query += ' ORDER BY deadline ASC'

            self.cursor.execute(query, params)
            return [dict(row) for row in self.cursor.fetchall()]

        except Exception as e:
            logger.error(f"Error getting homework: {e}")
            return []

    def get_homework_by_id(self, hw_id: int) -> Optional[Dict]:
        """Получить домашку по ID"""
        try:
            self.cursor.execute('SELECT * FROM homework WHERE id = ?', (hw_id,))
            row = self.cursor.fetchone()
            return dict(row) if row else None

        except Exception as e:
            logger.error(f"Error getting homework by ID: {e}")
            return None

    def delete_homework(self, hw_id: int):
        """Удалить домашку"""
        try:
            self.cursor.execute('DELETE FROM homework WHERE id = ?', (hw_id,))
            self.connection.commit()
            logger.info(f"Homework deleted: ID={hw_id}")

        except Exception as e:
            logger.error(f"Error deleting homework: {e}")
            raise

    def mark_homework_done(self, hw_id: int):
        """Отметить домашку как выполненную"""
        try:
            self.cursor.execute('''
                UPDATE homework 
                SET status = 'completed' 
                WHERE id = ?
            ''', (hw_id,))

            self.connection.commit()
            logger.info(f"Homework marked as done: ID={hw_id}")

        except Exception as e:
            logger.error(f"Error marking homework as done: {e}")
            raise

    def get_homework_by_subject(self, group_id: int, subject: str) -> List[Dict]:
        """Получить домашки по предмету"""
        try:
            self.cursor.execute('''
                SELECT * FROM homework 
                WHERE group_id = ? AND subject LIKE ? AND status = 'active'
                ORDER BY deadline ASC
            ''', (group_id, f'%{subject}%'))

            return [dict(row) for row in self.cursor.fetchall()]

        except Exception as e:
            logger.error(f"Error getting homework by subject: {e}")
            return []

    # ==================== PERSONAL TASKS ====================

    def add_personal_task(
            self,
            user_id: int,
            title: str,
            description: str = None,
            deadline: str = None,
            priority: str = 'medium'
    ) -> int:
        """Добавить личную задачу"""
        try:
            self.cursor.execute('''
                INSERT INTO personal_tasks (user_id, title, description, deadline, priority)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, title, description, deadline, priority))

            self.connection.commit()
            task_id = self.cursor.lastrowid

            logger.info(f"Personal task added: ID={task_id}, user={user_id}")
            return task_id

        except Exception as e:
            logger.error(f"Error adding personal task: {e}")
            raise

    def get_personal_tasks(self, user_id: int, status: str = 'active') -> List[Dict]:
        """Получить личные задачи пользователя"""
        try:
            query = 'SELECT * FROM personal_tasks WHERE user_id = ?'
            params = [user_id]

            if status:
                query += ' AND status = ?'
                params.append(status)

            query += ' ORDER BY deadline ASC'

            self.cursor.execute(query, params)
            return [dict(row) for row in self.cursor.fetchall()]

        except Exception as e:
            logger.error(f"Error getting personal tasks: {e}")
            return []

    def mark_personal_task_done(self, task_id: int):
        """Отметить личную задачу как выполненную"""
        try:
            self.cursor.execute('''
                UPDATE personal_tasks 
                SET status = 'completed', completed_at = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), task_id))

            self.connection.commit()
            logger.info(f"Personal task marked as done: ID={task_id}")

        except Exception as e:
            logger.error(f"Error marking personal task as done: {e}")
            raise

    def delete_personal_task(self, task_id: int):
        """Удалить личную задачу"""
        try:
            self.cursor.execute('DELETE FROM personal_tasks WHERE id = ?', (task_id,))
            self.connection.commit()
            logger.info(f"Personal task deleted: ID={task_id}")

        except Exception as e:
            logger.error(f"Error deleting personal task: {e}")
            raise

    # ==================== STATISTICS ====================

    def get_group_stats(self, group_id: int) -> Dict:
        """Получить статистику группы"""
        try:
            # Всего домашек
            self.cursor.execute('''
                SELECT COUNT(*) FROM homework WHERE group_id = ?
            ''', (group_id,))
            total = self.cursor.fetchone()[0]

            # Активные
            self.cursor.execute('''
                SELECT COUNT(*) FROM homework WHERE group_id = ? AND status = 'active'
            ''', (group_id,))
            active = self.cursor.fetchone()[0]

            # Выполненные
            self.cursor.execute('''
                SELECT COUNT(*) FROM homework WHERE group_id = ? AND status = 'completed'
            ''', (group_id,))
            completed = self.cursor.fetchone()[0]

            # Самый активный участник
            self.cursor.execute('''
                SELECT username, COUNT(*) as count
                FROM homework 
                WHERE group_id = ?
                GROUP BY username
                ORDER BY count DESC
                LIMIT 1
            ''', (group_id,))

            top_user = self.cursor.fetchone()

            return {
                'total': total,
                'active': active,
                'completed': completed,
                'top_user': dict(top_user) if top_user else None
            }

        except Exception as e:
            logger.error(f"Error getting group stats: {e}")
            return {'total': 0, 'active': 0, 'completed': 0, 'top_user': None}

    def close(self):
        """Закрыть соединение с БД"""
        self.connection.close()
        logger.info("Database connection closed")