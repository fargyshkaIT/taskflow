import sqlite3

# Подключаемся к базе данных. Если файла database.db нет, скрипт создаст его сам.
connection = sqlite3.connect('database.db')
cursor = connection.cursor()

# Создаем таблицу пользователей (users)
# id — первичный ключ с автоприростом (PRIMARY KEY AUTOINCREMENT)
# username — логин, имеет ограничение UNIQUE (база сама запретит создавать дубликаты логинов)
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
''')

# Создаем таблицу задач (tasks)
# user_id — числовое поле, связывающее задачу с пользователем
# FOREIGN KEY (Внешний ключ) связывает поле user_id в текущей таблице с полем id в таблице users.
# Это организует архитектурную связь «один-ко-многим».
cursor.execute('''
CREATE TABLE IF NOT EXISTS tasks (
id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    status TEXT NOT NULL,
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
''')

# Добавляем стандартного тестового админа, чтобы можно было войти без регистрации
try:
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', '1234'))
except sqlite3.IntegrityError:
    # Блок предотвратит падение скрипта, если база запускается повторно и admin уже существует
    pass

connection.commit() # Записываем все таблицы на диск
connection.close() # Закрываем соединение

print("База данных успешно настроена!")