import sqlite3

def create_database():
    # Подключение к базе данных (или создание новой, если она не существует)
    conn = sqlite3.connect('chat_links.db')
    
    # Создание курсора
    cursor = conn.cursor()
    
    # Создание таблицы chat_links, если она еще не существует
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_links (
        chat_id INTEGER PRIMARY KEY,
        admin_chat_id INTEGER NOT NULL
    )
    ''')
    
    # Сохранение изменений и закрытие соединения
    conn.commit()
    conn.close()
    print("База данных и таблица успешно созданы.")

# Вызов функции
create_database()
