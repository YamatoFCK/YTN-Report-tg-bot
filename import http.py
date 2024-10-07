import logging
import uuid
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
import sqlite3


# Включение логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
chat_links = {}


# Функция для подключения к базе данных
def get_db_connection():
    try:
        conn = sqlite3.connect('chat_links.db')
        print("Successfully connected to the database.")
        return conn
    except sqlite3.Error as e:
        print(f"Database connection failed: {e}")
        return None
    
# Получение ID админского чата для данного чата
def get_admin_chat_id(chat_id):
    conn = get_db_connection()
    if conn is None:
        print("Error connecting to database in get_admin_chat_id")
        return None

    cursor = conn.cursor()
    cursor.execute('SELECT admin_chat_id FROM chat_links WHERE chat_id = ?', (chat_id,))
    result = cursor.fetchone()
    conn.close()

    if result is not None:
        return result[0]  # Возвращаем admin_chat_id
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Добавить в чат", url="https://t.me/ReportYTN_bot?startgroup&admin=restrict_members+delete_messages+invite_users+pin_messages+manage_topics")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! Чтобы начать пользоваться ботом, добавь меня в свой чат и сделай админом. После этого используй команду /set для привязки админского чата.",
        reply_markup=reply_markup
    )

    # Проверка, является ли пользователь администратором
async def is_user_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Получаем список администраторов чата
    admins = await context.bot.get_chat_administrators(chat_id)
    
    # Проверяем, есть ли пользователь в списке администраторов
    for admin in admins:
        if admin.user.id == user_id:
            return True
    return False

# Проверка, привязан ли чат
def is_chat_linked(chat_id):
    conn = get_db_connection()
    if conn is None:
        print("Error connecting to database in is_chat_linked")
        return False

    cursor = conn.cursor()
    cursor.execute('SELECT admin_chat_id FROM chat_links WHERE chat_id = ?', (chat_id,))
    result = cursor.fetchone()

    # Логируем результат проверки
    print(f"Checking link for chat {chat_id}: {result}")

    if result is None:
        return False
    return True

# Функция привязки админского чата
async def set_admin_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 1:
        chat_id = update.effective_chat.id
        admin_chat_id = int(context.args[0])

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO chat_links (chat_id, admin_chat_id) VALUES (?, ?)', (chat_id, admin_chat_id))
        conn.commit()
        conn.close()

        await update.message.reply_text(f"Админский чат {admin_chat_id} успешно привязан к чату {chat_id}.")
    else:
        await update.message.reply_text("Пожалуйста, укажите ID админского чата.")

# Функция привязки админского чата
async def set_admin_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_user_admin(update, context):
        if len(context.args) == 1:
            chat_id = update.effective_chat.id
            admin_chat_id = int(context.args[0])

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO chat_links (chat_id, admin_chat_id) VALUES (?, ?)', (chat_id, admin_chat_id))
            conn.commit()
            conn.close()

            await update.message.reply_text(f"Админский чат {admin_chat_id} успешно привязан к чату {chat_id}.")
        else:
            await update.message.reply_text("Пожалуйста, укажите ID админского чата.")
    else:
        await update.message.reply_text("Эта команда доступна только администраторам.")

# Команда для удаления чата
async def remove_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_user_admin(update, context):
        chat_id = update.effective_chat.id

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM chat_links WHERE chat_id = ?', (chat_id,))
        conn.commit()
        conn.close()

        await update.message.reply_text(f"Связь с чатом {chat_id} успешно удалена.")
    else:
        await update.message.reply_text("Эта команда доступна только администраторам.")


# Команда /id для получения ID чата

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_member = await update.effective_chat.get_member(user.id)

    if chat_member.status not in ['administrator', 'creator']:
        await update.message.reply_text("Эта команда доступна только администраторам.")
        return

    chat_id = update.effective_chat.id
    await update.message.reply_text(f"ID этого чата: `{chat_id}`", parse_mode='Markdown')

#Реепоророрт
import uuid

import uuid

async def report_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if is_chat_linked(chat_id):
        admin_chat_id = get_admin_chat_id(chat_id)
        message = update.message
        reported_user = message.reply_to_message.from_user if message.reply_to_message else None

        if reported_user:
            reporter = update.message.from_user

            # Проверка: нельзя репортить самого себя
            if reporter.id == reported_user.id:
                await update.message.reply_text("Вы не можете репортить самого себя.")
                return

            # Получаем список администраторов чата
            chat_admins = await context.bot.get_chat_administrators(chat_id)
            admin_ids = [admin.user.id for admin in chat_admins]

            # Проверка: нельзя репортить администратора
            if reported_user.id in admin_ids:
                await update.message.reply_text("Вы не можете репортить администратора.")
                return

            # Создаем уникальный номер репорта с помощью UUID
            report_id = str(uuid.uuid4())[:8]  # Первые 8 символов UUID

            # Отправляем сообщение с ID сообщения в callback_data
            reported_message_id = message.reply_to_message.message_id if message.reply_to_message else message.message_id
            link = f"https://t.me/c/{str(chat_id)[4:]}/{reported_message_id}"

            # Формируем ссылки на профили репортера и нарушителя
            reporter_link = f'<a href="tg://user?id={reporter.id}">{reporter.first_name}</a>'
            reported_user_link = f'<a href="tg://user?id={reported_user.id}">{reported_user.first_name}</a>' if reported_user else 'неизвестно'

            try:
                # Отправляем сообщение модератору
                sent_message = await context.bot.send_message(
                    chat_id=admin_chat_id,
                    text=(f"<b>Репорт #{report_id}</b>\n"
                          f"Чат: <b>{update.effective_chat.title}</b>\n"
                          f"Репортер: {reporter_link}\n"
                          f"Нарушитель: {reported_user_link}\n"
                          f"Посмотреть сообщение: <a href='{link}'>ссылка</a>"),
                    parse_mode="HTML"
                )

                # Передаем ID сообщения в callback_data
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"Решить репорт #{report_id}", callback_data=f"resolve_{report_id}_{admin_chat_id}_{sent_message.message_id}")]
                ])

                # Обновляем сообщение с кнопкой
                await context.bot.edit_message_reply_markup(
                    chat_id=admin_chat_id,
                    message_id=sent_message.message_id,
                    reply_markup=keyboard
                )

                await update.message.reply_text(f"Репорт #{report_id} был отправлен модераторам.")
            except Exception as e:
                print(f"Ошибка при отправке сообщения: {e}")
                await update.message.reply_text("Ошибка при отправке репорта.")
        else:
            await update.message.reply_text("Пожалуйста, ответьте на сообщение пользователя, на которого хотите пожаловаться.")
    else:
        await update.message.reply_text("Этот чат не привязан к админскому чату. Используйте команду /set для привязки.")

# Обработчик для решения репорта
async def resolve_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Разбираем данные из callback_data
    data = query.data.split("_")
    report_id = data[1]  # Номер репорта
    admin_chat_id = data[2]
    message_id = data[3]  # Получаем message_id из callback_data

    try:
        # Логируем попытку редактирования
        print(f"Попытка редактирования сообщения {message_id} в чате {admin_chat_id}")

        # Попытка редактирования сообщения
        await context.bot.edit_message_text(
            chat_id=admin_chat_id,
            message_id=int(message_id),
            text=f"Репорт #{report_id} рассмотрен✅️"
        )

        # Успешное редактирование, меняем текст кнопки
        await query.edit_message_text(f"Репорт #{report_id} рассмотрен администратором✅️")
    except Exception as e:
        # Логируем ошибку
        print(f"Ошибка при изменении сообщения: {e}")
        
        # Если сообщение нельзя отредактировать, отправляем новое сообщение
        await context.bot.send_message(
            chat_id=admin_chat_id,
            text=f"Репорт #{report_id} рассмотрен✅️"
        )

        # Меняем текст кнопки, даже если пришлось отправить новое сообщение
        await query.edit_message_text(f"Репорт #{report_id} рассмотрен администратором✅️")


# Команда для обновления админского чата
async def update_admin_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_user_admin(update, context):
        if len(context.args) == 1:
            chat_id = update.effective_chat.id
            new_admin_chat_id = int(context.args[0])

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE chat_links SET admin_chat_id = ? WHERE chat_id = ?', (new_admin_chat_id, chat_id))
            conn.commit()
            conn.close()

            await update.message.reply_text(f"Админский чат успешно обновлен на {new_admin_chat_id}.")
        else:
            await update.message.reply_text("Пожалуйста, укажите новый ID админского чата.")
    else:
        await update.message.reply_text("Эта команда доступна только администраторам.")

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "/set [ID] - Привязка админского чата\n"
        "/update [ID] - Обновление ID админского чата\n"
        "/remove - Удаление связи с админским чатом\n"
        'Полная <a href="https://telegra.ph/Kak-isplolzovat-ReportYTN-bot-10-03">инструкция</a>'
    )
    await update.message.reply_text(help_text, parse_mode='HTML')




# Основная функция для запуска бота
timeout = httpx.Timeout(10.0)
client = httpx.AsyncClient(timeout=timeout)

application = ApplicationBuilder().token('7991658997:AAGBxo7u1VZ_3huqPcmynFNHVjBir_Is0gs').build()
application.httpx_client = client

# Обработка команд бота
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("set", set_admin_chat))
application.add_handler(CommandHandler("update", update_admin_chat))
application.add_handler(CommandHandler("remove", remove_chat))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("id", get_chat_id))
application.add_handler(CommandHandler('report', report_message))
application.add_handler(CallbackQueryHandler(resolve_report, pattern=r'resolve_\\d+'))
application.add_handler(CallbackQueryHandler(resolve_report))

# Запуск бота
application.run_polling()
