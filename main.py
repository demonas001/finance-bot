from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from datetime import datetime, timedelta
import psycopg2
import logging

# Включаем логирование, чтобы отлавливать ошибки
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)  # Уровень логирования: INFO (информационные сообщения)
logger = logging.getLogger(__name__)

# Connect to database
def create_connection():
    conn = psycopg2.connect(
        dbname="finance-bot",
        user="postgres",
        password="t52H3zu9",
        host="finance-db", #change for docker
        port=5432
    )
    return conn  # Our conn name

# Функция для обработки команды /start
async def start(update: Update, context: CallbackContext):  # <-- Добавлен async
    user = update.message.from_user  # get user data
    await update.message.reply_text(f"Привет, {user.first_name}! Я твой финансовый бот. Введи команду /help, чтобы узнать, что я умею.")  # <-- Добавлен await
async def report(update: Update, context: CallbackContext):
    try:
        # Получаем аргументы (например, "day", "week", "month")
        period = context.args[0] if context.args else "day"
        
        # Подключаемся к базе данных
        conn = create_connection()
        cursor = conn.cursor()
        
        # Получаем текущую дату
        today = datetime.today()
        
        if period == "day":
            start_date = today
            end_date = today + timedelta(days=1)
        elif period == "week":
            start_date = today - timedelta(days=today.weekday())  # Начало недели (понедельник)
            end_date = start_date + timedelta(weeks=1)  # Конец недели
        elif period == "month":
            start_date = today.replace(day=1)  # Первый день месяца
            end_date = (start_date.replace(month=today.month + 1) if today.month != 12 else start_date.replace(year=today.year + 1, month=1))  # Первый день следующего месяца
        else:
            await update.message.reply_text("Пожалуйста, укажи корректный период: day, week или month.")
            return
        
        # Выполняем запрос для получения всех записей за выбранный период
        cursor.execute("""
            SELECT amount, description, created_at 
            FROM expenses
            WHERE created_at BETWEEN %s AND %s
        """, (start_date, end_date))

        records = cursor.fetchall()  # Получаем все записи

        if records:
            total = sum([record[0] for record in records])  # Суммируем все расходы
            report_text = f"Отчет за период с {start_date.strftime('%d-%m-%Y')} по {end_date.strftime('%d-%m-%Y')}:\n"
            report_text += "\n".join([f"{record[1]}: {record[0]}" for record in records])  # Список расходов
            report_text += f"\n\nОбщая сумма: {total} UAH"
            await update.message.reply_text(report_text)
        else:
            await update.message.reply_text("Нет записей за этот период.")
        
        # Закрываем соединение с базой данных
        cursor.close()
        conn.close()

    except Exception as e:
        logger.error(f"Ошибка при получении отчета: {e}")
        await update.message.reply_text("Произошла ошибка при обработке отчета.")
# Функция для обработки команды /help
async def help_command(update: Update, context: CallbackContext):  # <-- Добавлен async
    await update.message.reply_text("Я помогу тебе вести учет расходов и доходов. Введи команду /add для добавления записи.")  # <-- Добавлен await

# Команда /add — добавляет запись о расходах в базу данных
async def add_record(update: Update, context: CallbackContext):  # <-- Добавлен async
    try:
        # Извлекаем аргументы из команды (сумма и описание)
        amount = float(context.args[0])  # Преобразуем первый аргумент в число (сумма)
        description = ' '.join(context.args[1:])  # Оставшиеся аргументы — это описание

        # Создаем соединение с базой данных
        conn = create_connection()
        cursor = conn.cursor()  # Создаем курсор для работы с запросами

        # Выполняем SQL-запрос для вставки данных в таблицу expenses
        cursor.execute("INSERT INTO expenses (amount, description) VALUES (%s, %s)", (amount, description))
        conn.commit()  # Подтверждаем изменения в базе данных

        cursor.close()  # Закрываем курсор
        conn.close()  # Закрываем соединение с базой данных

        await update.message.reply_text(f"Запись добавлена: {amount} — {description}")  # <-- Добавлен await

    except IndexError:
        await update.message.reply_text("Пожалуйста, укажи сумму и описание.")  # Если не указаны аргументы
    except ValueError:
        await update.message.reply_text("Неверный формат суммы.")  # Если сумма введена неправильно (например, буквы)

        # Команда /all — выводит все записи
async def all_records(update: Update, context: CallbackContext):
    try:
        # Создаем соединение с базой данных
        conn = create_connection()
        cursor = conn.cursor()
        
        # Выполняем запрос для получения всех записей
        cursor.execute("SELECT id, amount, description, created_at FROM expenses")
        
        records = cursor.fetchall()
        
        if records:
            all_records_text = "Все записи:\n"
            for record in records:
                all_records_text += f"ID: {record[0]} | {record[1]} — {record[2]} | {record[3]}\n"
            await update.message.reply_text(all_records_text)
        else:
            await update.message.reply_text("Нет записей в базе данных.")
        
        # Закрываем соединение с базой данных
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Ошибка при получении записей: {e}")
        await update.message.reply_text("Произошла ошибка при обработке запроса.")

# Основная функция для запуска бота
def main():
    TOKEN = '8094361830:AAHBMjbsVVDoxOpJLTVbrGxHZNsDqOf3Sfw'  # Укажи свой токен API Telegram
    # Создаем объект Application, который обрабатывает обновления от Telegram
    application = Application.builder().token(TOKEN).build()  # <-- Изменено: используем Application

    # Регистрируем обработчики команд, которые будет обрабатывать бот
    application.add_handler(CommandHandler("start", start))  # Обработчик для команды /start
    application.add_handler(CommandHandler("help", help_command))  # Обработчик для команды /help
    application.add_handler(CommandHandler("add", add_record))  # Обработчик для команды /add
    application.add_handler(CommandHandler("all", all_records))  # Обработчик для команды /add
    application.add_handler(CommandHandler("report", report))  # Обработчик для команды /add
    # Запускаем бота
    application.run_polling()  # <-- Изменено: используем run_polling вместо start_polling

# Точка входа в программу
if __name__ == '__main__':
    main()  # Запуск основной функции
