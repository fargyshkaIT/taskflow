# Импортируем инструменты из библиотеки Flask:
# Flask — каркас для создания веб-приложения
# render_template — функция, которая берет HTML-файл из папки templates и показывает его в браузере
# request — объект, который хранит всё, что ввел пользователь в формы на сайте
# redirect — перенаправляет пользователя на другую страницу (маршрут)
# url_for — умный помощник, который строит ссылки на основе названий функций бэкенда
# session — сессии (куки) для запоминания пользователя (чтобы сайт "помнил", кто вошел)
# flash — механизм для отправки коротких всплывающих сообщений (ошибок) на страницу
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import re  # Импортируем регулярные выражения (нужны для сложной проверки надежности пароля)

# Создаем экземпляр веб-приложения
app = Flask(__name__)

# Секретный ключ. Он нужен Flask для надежного шифрования данных сессий в браузере.
# Без него сессии выдадут ошибку, а хакеры смогут подделать ID пользователя в куках.
app.secret_key = 'qwore_secret_key'


# -------------------------------------------------------------
# 1. МАРШРУТ: ГЛАВНАЯ СТРАНИЦА (Корень сайта "/")
# -------------------------------------------------------------
@app.route('/')
def index():
    # Проверяем: если в сессии уже записан 'user_id', значит пользователь ранее успешно входил.
    if 'user_id' in session:
        # Перенаправляем его сразу в личный кабинет (на функцию dashboard)
        return redirect(url_for('dashboard'))
    # Если пользователя в сессии нет — отправляем его на страницу авторизации
    return redirect(url_for('login'))


# -------------------------------------------------------------
# 2. МАРШРУТ: АВТОРИЗАЦИЯ (ВХОД НА САЙТ)
# -------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        input_login = request.form.get('username')
        input_password = request.form.get('password')

        # Подключаемся к базе данных
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Шаг 1: Ищем пользователя ТОЛЬКО по его логину
        cursor.execute("SELECT id, password FROM users WHERE username = ?", (input_login,))
        user_data = cursor.fetchone()  # Вернет кортеж (id, password) или None
        conn.close()

        # Шаг 2: Если пользователь с таким логином вообще существует
        if user_data:
            db_id = user_data[0]  # Достаем его реальный ID из базы
            db_password = user_data[1]  # Достаем его реальный правильный пароль из базы

            # Шаг 3: Жестко сравниваем введенный пароль с паролем из базы данных
            if input_password == db_password:
                # Если они совпали на 100% — пускаем на сайт
                session['user_id'] = db_id
                session['username'] = input_login
                return redirect(url_for('dashboard'))
            else:
                # Если логин существует, но пароль не подошел
                flash("Неверный логин или пароль! Попробуйте снова.")
                return render_template('login.html')
        else:
            # Если пользователя с таким логином вообще нет в базе
            flash("Неверный логин или пароль! Попробуйте снова.")
            return render_template('login.html')

    return render_template('login.html')


# -------------------------------------------------------------
# 3. МАРШРУТ: РЕГИСТРАЦИЯ С ВАЛИДАЦИЕЙ И АВТОВХОДОМ
# -------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_login = request.form.get('username', '')
        user_pwd = request.form.get('password', '')

        # --- БЛОК ВАЛИДАЦИИ (ПРОВЕРКИ) ПАРОЛЯ ---
        # 1. Проверяем длину пароля (не менее 8 символов)
        if len(user_pwd) < 8:
            flash("Пароль должен быть не менее 8 символов!")
            return render_template('register.html')

        # 2. Ищем через регулярное выражение хотя бы одну цифру от 0 до 9
        if not re.search(r"[0-9]", str(user_pwd)):
            flash("Пароль должен содержать хотя бы одну цифру (0-9)!")
            return render_template('register.html')

        # 3. Ищем хотя бы одну заглавную букву (поддерживает и английский, и русский алфавит)
        if not re.search(r"[A-ZА-Я]", str(user_pwd)):
            flash("Пароль должен содержать хотя бы одну заглавную букву!")
            return render_template('register.html')

        # 4. Ищем хотя бы одну строчную (маленькую) букву
        if not re.search(r"[a-zа-я]", str(user_pwd)):
            flash("Пароль должен содержать хотя бы одну строчную букву!")
            return render_template('register.html')

        # --- СОХРАНЕНИЕ В БАЗУ ДАННЫХ И АВТОВХОД ---
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        try:
            # Записываем нового пользователя (логин и проверенный пароль) в таблицу users
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user_login, user_pwd))
            conn.commit()  # Сохраняем изменения в файле базы данных

            # Сразу вытаскиваем ID только что зарегистрированного пользователя
            cursor.execute("SELECT id FROM users WHERE username = ?", (user_login,))
            new_user_data = cursor.fetchone()
            conn.close()

            # Если ID успешно получен, автоматически авторизуем пользователя (записываем в сессию бэкенда)
            if new_user_data:
                session['user_id'] = new_user_data[0]  # Индекс [0] убирает скобки, берем чистое число
                session['username'] = user_login

            # Перенаправляем пользователя сразу на его новую, чистую панель задач!
            return redirect(url_for('dashboard'))

        except sqlite3.IntegrityError:
            # Ошибка сработает автоматически, если такой логин уже есть в базе (благодаря правилу UNIQUE в БД)
            conn.close()
            flash("Этот логин уже занят! Придумайте другой.")
            return render_template('register.html')

    return render_template('register.html')


# -------------------------------------------------------------
# 4. МАРШРУТ: ЛИЧНЫЙ КАБИНЕТ И СПИСОК ЗАДАЧ
# -------------------------------------------------------------
@app.route('/dashboard')
def dashboard():
    # Защита личного кабинета от гостей: если 'user_id' нет в сессии, то не пускаем
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Выкидываем взломщика на страницу входа

    current_user_id = session['user_id']  # Извлекаем ID текущего авторизованного юзера

    # Запрашиваем из базы данных задачи, которые принадлежат ТОЛЬКО ЭТОМУ пользователю
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, status FROM tasks WHERE user_id = ?", (current_user_id,))
    user_tasks = cursor.fetchall()  # fetchall() забирает ВСЕ строки в виде списка кортежей
    conn.close()

    # Открываем HTML-страницу дашборда и передаем внутрь переменную tasks со списком задач
    return render_template('dashboard.html', tasks=user_tasks)


# -------------------------------------------------------------
# 5. МАРШРУТ: ДОБАВЛЕНИЕ НОВОЙ ЗАДАЧИ
# -------------------------------------------------------------
@app.route('/add_task', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    task_title = request.form.get('task_title')  # Забираем текст задачи из формы
    task_status = 'План'  # Автоматически даем новой задаче статус 'План'
    current_user_id = session['user_id']  # Узнаем, кто именно создает задачу

    # Записываем задачу в таблицу tasks, связывая её с пользователем через user_id
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (title, status, user_id) VALUES (?, ?, ?)",
                   (task_title, task_status, current_user_id))
    conn.commit()  # Сохраняем изменения на диске
    conn.close()

    # Перезагружаем страницу личного кабинета, чтобы пользователь сразу увидел новую задачу
    return redirect(url_for('dashboard'))


# -------------------------------------------------------------
# 6. МАРШРУТ: УДАЛЕНИЕ ЗАДАЧИ (Реализация полной CRUD-системы)
# -------------------------------------------------------------
# В адресе ссылки <int:task_id> — это динамический параметр. Он автоматически ловит ID задачи
@app.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Двойная проверка безопасности: удаляем задачу, где совпадает и её ID, и ID текущего юзера.
    # Это защищает от уязвимости, когда чужой пользователь пытается вручную подставить чужой ID задачи в ссылку.
    cursor.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, session['user_id']))
    conn.commit()
    conn.close()

    # Возвращаем пользователя на обновленный дашборд
    return redirect(url_for('dashboard'))


# -------------------------------------------------------------
# 7. МАРШРУТ: ВЫХОД ИЗ СИСТЕМЫ (РАЗЛОГИН)
# -------------------------------------------------------------
@app.route('/logout')
def logout():
    session.clear()  # Полностью очищаем сессию бэкенда (сервер начисто забывает пользователя)
    return redirect(url_for('login'))  # Перенаправляем на пустую форму входа


# ТОЧКА ВХОДА В ПРОГРАММУ
if __name__ == '__main__':
    # debug=True активирует горячую перезагрузку кода при изменениях
    # и выводит подробные отчеты об ошибках прямо в окно браузера
    app.run(debug=True)
