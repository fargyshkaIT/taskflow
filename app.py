# Импортируем только те инструменты Flask, которые реально используются:
# Flask — каркас веб-приложения
# render_template — отображает HTML-страницы из папки templates
# request — принимает данные (текст задачи), которые вводит пользователь
# redirect — перенаправляет браузер на другой адрес
# url_for — строит ссылки на основе названий функций бэкенда
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os  # Импортируем системный модуль для проверки существования файла базы данных

app = Flask(__name__)

# Путь к файлу базы данных в папке проекта
DATABASE_FILE = 'database.db'
# Фиксированный ID пользователя. Все задачи будут записываться на admin с ID = 1
ADMIN_USER_ID = 1


# -------------------------------------------------------------
# ФУНКЦИЯ ИНИЦИАЛИЗАЦИИ БАЗЫ ДАННЫХ (Вызывается автоматически)
# -------------------------------------------------------------
def init_db():
    """Создает базу данных и таблицы, если они еще не созданы."""
    # Проверяем, существует ли уже файл database.db на компьютере
    if not os.path.exists(DATABASE_FILE):
        # Подключаемся к базе (создаем пустой файл)
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Создаем таблицу пользователей (users) для связей. id = 1 будет у admin.
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE
        )
        ''')

        # Создаем таблицу задач (tasks). Поле user_id связывает её с таблицей пользователей.
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            status TEXT NOT NULL,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')

        # Сразу добавляем в базу единственного пользователя admin с ID = 1
        cursor.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (ADMIN_USER_ID, 'admin'))

        conn.commit()  # Сохраняем изменения на диске
        conn.close()  # Закрываем базу данных
        print("База данных успешно создана прямо при старте приложения!")


# Вызываем функцию создания базы данных перед запуском маршрутов
init_db()


# -------------------------------------------------------------
# 1. МАРШРУТ: ГЛАВНАЯ СТРАНИЦА (Корень сайта "/")
# -------------------------------------------------------------
@app.route('/')
def index():
    # Когда пользователь заходит на http://127.0.0,
    # мы мгновенно перенаправляем его в личный кабинет со списком задач
    return redirect(url_for('dashboard'))


# -------------------------------------------------------------
# 2. МАРШРУТ: ПАНЕЛЬ ЗАДАЧ (ВЫВОД НА ЭКРАН)
# -------------------------------------------------------------
@app.route('/dashboard')
def dashboard():
    # Открываем соединение с файлом базы данных SQLite
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Запрашиваем из таблицы tasks задачи, принадлежащие только admin (user_id = 1)
    # Знак вопроса — безопасный плейсхолдер для защиты от вредоносного кода
    cursor.execute("SELECT id, title, status FROM tasks WHERE user_id = ?", (ADMIN_USER_ID,))
    user_tasks = cursor.fetchall()  # Забираем ВСЕ найденные строки в виде списка кортежей
    conn.close()  # Закрываем базу данных, освобождая оперативную память

    # Отдаем браузеру страницу dashboard.html и передаем внутрь переменную tasks с нашими задачами
    return render_template('dashboard.html', tasks=user_tasks)


# -------------------------------------------------------------
# 3. МАРШРУТ: ДОБАВЛЕНИЕ НОВОЙ ЗАДАЧИ
# -------------------------------------------------------------
@app.route('/add_task', methods=['POST'])
def add_task():
    # request.form.get вытаскивает текст, который пользователь написал в инпуте с name="task_title"
    task_title = request.form.get('task_title')
    task_status = 'План'  # Всем новым задачам по умолчанию жестко ставим статус 'План'

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    # Записываем задачу в базу данных, привязывая её к ADMIN_USER_ID (1)
    cursor.execute("INSERT INTO tasks (title, status, user_id) VALUES (?, ?, ?)",
                   (task_title, task_status, ADMIN_USER_ID))
    conn.commit()  # Обязательно сохраняем изменения на жестком диске!
    conn.close()

    # Перезагружаем страницу — возвращаем пользователя на дашборд, чтобы он увидел добавленный таск
    return redirect(url_for('dashboard'))


# -------------------------------------------------------------
# 4. МАРШРУТ: УДАЛЕНИЕ ЗАДАЧИ (Полный CRUD)
# -------------------------------------------------------------
# В URL мы передаем параметр <int:task_id>. Flask сам превратит его в число и передаст в функцию
@app.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    # Находим в таблице задачу по её уникальному id и удаляем строку
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()  # Фиксируем удаление в файле
    conn.close()

    # Возвращаем пользователя на дашборд, где список задач уже обновился
    return redirect(url_for('dashboard'))


# ТОЧКА ВХОДА В ПРОГРАММУ
if __name__ == '__main__':
    # debug=True автоматически перезапускает локальный сервер, если ты изменил код в PyCharm
    app.run(debug=True)
