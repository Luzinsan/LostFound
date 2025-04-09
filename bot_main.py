import logging
from telegram.constants import ParseMode
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters,
    JobQueue,
)

from indexing.tasks import search_index_task, search_all_cities_task
from celery.result import AsyncResult

TELEGRAM_BOT_TOKEN = "7734880573:AAEbhW6NXoz3DtXkpjAT-BEJGGR4vzRfkWk"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ----------- Глобальные константы / состояния для ConversationHandler -----------
ST_CITY = 1
ST_TYPE = 2
ST_QUERY = 3

AVAILABLE_CITIES = ["Москва", "Санкт-Петербург", "Нижний Новгород"]
AVAILABLE_TYPES = [
    "restaurant","cafe","tourist_attraction","museum","performing_arts_theater",
    "historical_place","art_gallery","park","lodging","church"
]


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привет! Я бот Lost & Found.\n"
        "Вот что я умею:\n"
        "- /search <город> <запрос> — быстрый поиск\n"
        "- /searchall <запрос> — поиск по всем городам\n"
        "- /startsearch — пошаговый поиск с выбором города и типа места\n"
        "- /help — показать помощь\n"
        "Просто напиши сообщение, и я выдам подсказку!"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Список доступных команд:\n"
        "/search <город> <запрос> - поиск по одному городу\n"
        "/searchall <запрос> - поиск по всем городам\n"
        "/startsearch - пошаговый диалоговый поиск\n"
        "/help - помощь по командам\n"
        "Пример: /search Москва museum\n"
    )

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("Формат: /search <город> <запрос>")
            return

        city = args[0]
        query = " ".join(args[1:])
        # Синхронный вызов
        task_result = search_index_task.delay(city, query, limit=10)
        response = task_result.get(timeout=15)

        if response and response.get("status") == "success":
            results = response.get("results", [])
            total_found = response.get("total_found", 0)
            message_text = f"Найдено результатов: {total_found}\n"

            for idx, place in enumerate(results[:10], start=1):
                name = place.get("name", "???")
                address = place.get("address", "")
                score = place.get("combined_score", 0)
                summary = place.get("summary", "")
                message_text += (
                    f"\n<b>{idx}. {name}</b>\n"
                    f"Адрес: {address}\n"
                    f"Скор: {score:.2f}\n"
                    f"{summary}\n"
                )
            await update.message.reply_text(message_text, parse_mode=ParseMode.HTML)
        else:
            msg = response.get("message", "Неизвестная ошибка") if response else "Нет ответа"
            await update.message.reply_text(f"Ошибка: {msg}")

    except Exception as e:
        logger.exception("search_command error:")
        await update.message.reply_text("Произошла ошибка при поиске (см. логи).")


async def search_all_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        args = context.args
        if not args:
            await update.message.reply_text("Формат: /searchall <запрос>")
            return

        query = " ".join(args)
        task_result = search_all_cities_task.delay(query, limit=10)
        response = task_result.get(timeout=20)

        if response and response.get("status") == "success":
            results = response.get("results", [])
            total_found = response.get("total_found", 0)
            message_text = f"Найдено результатов (по всем городам): {total_found}\n"

            for idx, place in enumerate(results[:10], start=1):
                city = place.get("city", "???")
                name = place.get("name", "???")
                address = place.get("address", "")
                score = place.get("combined_score", 0)
                summary = place.get("summary", "")
                message_text += (
                    f"\n<b>{idx}. {name}</b> ({city})\n"
                    f"Адрес: {address}\n"
                    f"Скор: {score:.2f}\n"
                    f"{summary}\n"
                )
            await update.message.reply_text(message_text, parse_mode=ParseMode.HTML)
        else:
            msg = response.get("message", "Неизвестная ошибка") if response else "Нет ответа"
            await update.message.reply_text(f"Ошибка: {msg}")

    except Exception as e:
        logger.exception("search_all_command error:")
        await update.message.reply_text("Произошла ошибка при поиске (см. логи).")


async def check_task_result(context: ContextTypes.DEFAULT_TYPE):
    """
    Ф-ция для JobQueue: проверяет готовность задачи Celery.
    Если готова — отправляет результат в чат, иначе перезапускается.
    """
    job_data = context.job.data  # словарь
    task_id = job_data["task_id"]
    chat_id = job_data["chat_id"]

    # Достаем результат
    res = AsyncResult(id=task_id)
    if res.ready():
        # Если задача завершена — получаем результат
        response = res.get()
        if response and response.get("status") == "success":
            results = response.get("results", [])
            total_found = response.get("total_found", 0)
            msg = f"Готово! Найдено результатов: {total_found}\n"
            for idx, place in enumerate(results[:10], start=1):
                name = place.get("name", "???")
                address = place.get("address", "")
                score = place.get("combined_score", 0)
                summary = place.get("summary", "")
                msg += (
                    f"\n<b>{idx}. {name}</b>\n"
                    f"Адрес: {address}\n"
                    f"Скор: {score:.2f}\n"
                    f"{summary}\n"
                )
            await context.bot.send_message(
                chat_id=chat_id, text=msg, parse_mode=ParseMode.HTML
            )
        else:
            # Задача закончилась, но вернула ошибку
            err_msg = response.get("message", "Ошибка") if response else "Неизвестная ошибка"
            await context.bot.send_message(chat_id=chat_id, text=f"Ошибка: {err_msg}")
        # Снимаем задачу с JobQueue, чтобы не перезапускать проверку
        context.job.schedule_removal()
    else:
        # Еще не готово — повторим через 5 секунд
        await context.bot.send_message(chat_id=chat_id, text="Поиск ещё продолжается...")
        context.job_queue.run_once(
            check_task_result,
            when=5,
            data=job_data
        )


async def startsearch_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Запуск «диалогового» поиска. Спросим у пользователя город.
    """
    await update.message.reply_text(
        "Начинаем пошаговый поиск.\nВыберите город:",
    )
    # Выведем inline-кнопки с тремя городами
    buttons = [
        [InlineKeyboardButton(city, callback_data=city)] for city in AVAILABLE_CITIES
    ]
    markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("Выберите город:", reply_markup=markup)
    return ST_CITY

async def city_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Пользователь нажал на inline-кнопку с городом.
    """
    query = update.callback_query
    await query.answer()  # обязательно, чтобы Telegram не «висел»
    chosen_city = query.data  # одно из AVAILABLE_CITIES
    context.user_data["chosen_city"] = chosen_city

    # Предлагаем выбрать тип места
    buttons = []
    row = []
    for i, place_type in enumerate(AVAILABLE_TYPES, start=1):
        row.append(InlineKeyboardButton(place_type, callback_data=place_type))
        # сделаем сетку 2 x N
        if i % 2 == 0:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    markup = InlineKeyboardMarkup(buttons)
    await query.edit_message_text(
        text=f"Вы выбрали город: {chosen_city}\nТеперь выберите тип места:",
        reply_markup=markup
    )
    return ST_TYPE

async def type_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Пользователь выбрал тип места (inline-кнопка).
    Теперь попросим ввести что-то текстом (доп. запрос).
    """
    query = update.callback_query
    await query.answer()
    chosen_type = query.data
    context.user_data["chosen_type"] = chosen_type

    await query.edit_message_text(
        text=f"Вы выбрали тип: {chosen_type}.\n"
             f"Если хотите уточнить запрос (например, 'с видом на реку'), введите это сообщением.\n"
             f"Или введите /skip, чтобы пропустить."
    )
    return ST_QUERY

async def query_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Пользователь ввел дополнительный текст запроса.
    """
    user_text = update.message.text
    context.user_data["additional_query"] = user_text

    await update.message.reply_text(
        "Принято! Запускаю поиск асинхронно..."
    )
    # Запустим Celery-задачу
    city = context.user_data["chosen_city"]
    place_type = context.user_data["chosen_type"]
    additional = context.user_data["additional_query"]

    # Собираем общий query. Условно place_type + additional
    # Если user_text пуст, пусть будет просто place_type
    full_query = f"{place_type} {additional}".strip()

    task = search_index_task.delay(city, full_query, limit=10)
    task_id = task.id

    # Добавим задачу в JobQueue, будем чекать каждые 5 сек
    context.job_queue.run_once(
        check_task_result,
        when=5,
        data={"task_id": task_id, "chat_id": update.effective_chat.id}
    )
    # Завершаем conversation
    return ConversationHandler.END

async def skip_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Пользователь пропускает ввод доп.запроса.
    """
    context.user_data["additional_query"] = ""
    await update.message.reply_text("Ок, без уточняющего запроса. Запускаю поиск...")

    city = context.user_data["chosen_city"]
    place_type = context.user_data["chosen_type"]
    full_query = place_type

    task = search_index_task.delay(city, full_query, limit=10)
    task_id = task.id

    # Запускаем асинхронную проверку
    context.job_queue.run_once(
        check_task_result,
        when=5,
        data={"task_id": task_id, "chat_id": update.effective_chat.id}
    )

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Если пользователь введет /cancel в любой момент, прерываем диалог.
    """
    await update.message.reply_text("Поиск отменен.")
    return ConversationHandler.END


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Любое текстовое сообщение, которое не попало в команду/хендлер.
    Просто логируем и даем подсказку.
    """
    user_text = update.message.text
    logger.debug(f"Пришло произвольное сообщение: {user_text!r}")
    await update.message.reply_text(
        "Я пока понимаю только /search, /searchall, /startsearch.\n"
        "Попробуй /help для списка команд."
    )


def main():
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        # .persistence(persistence)
        .build()
    )

    # --- ConversationHandler для пошагового поиска ---
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("startsearch", startsearch_command)],
        states={
            ST_CITY: [CallbackQueryHandler(city_chosen)],
            ST_TYPE: [CallbackQueryHandler(type_chosen)],
            ST_QUERY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, query_received),
                CommandHandler("skip", skip_query),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("searchall", search_all_command))

    # Добавляем диалог
    application.add_handler(conv_handler)

    # Общий обработчик для всего текста, который «не поймали» другие хендлеры
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    # Запуск
    application.run_polling()
    logger.info("Bot started!")


if __name__ == "__main__":
    main()
