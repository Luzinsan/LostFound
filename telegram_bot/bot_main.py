import os
import sys
import logging
import aiohttp
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
)

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from config import settings

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

ST_CITY = 1
ST_TYPE = 2
ST_QUERY = 3

# CONFIGS
AVAILABLE_CITIES = settings.CITIES
AVAILABLE_TYPES = settings.PLACE_TYPES
API_BASE = settings.API_BASE 
TELEGRAM_BOT_TOKEN = settings.TELEGRAM_BOT_API  

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привет! Я бот Lost & Found.\n"
        "Вот что я умею:\n"
        "- /search <город> <запрос> — быстрый поиск (по индексам)\n"
        "- /searchall <запрос> — поиск по всем городам (по индексам)\n"
        "- /semantic <город> <запрос> — семантический поиск по конкретному городу\n"
        "- /semanticall <запрос> — семантический поиск по всем городам\n"
        "- /startsearch — пошаговый поиск с выбором города\n"
        "- /help — показать помощь\n"
        "Просто напиши сообщение, и я выдам подсказку!"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Список доступных команд:\n"
        "/search <город> <запрос> - поиск по одному городу (индексный)\n"
        "/searchall <запрос> - поиск по всем городам (индексный)\n"
        "/semantic <город> <запрос> - семантический поиск по одному городу\n"
        "/semanticall <запрос> - семантический поиск по всем городам\n"
        "/startsearch - пошаговый диалоговый поиск\n"
        "/help - помощь по командам\n"
        "Пример: /search Москва museum  или  /semantic Москва интересный музей"
    )

# Индексный поиск
async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Пример команды: /search Москва museum
    Делает GET-запрос:
    GET {API_BASE}/api/v1/index_search/city/{city}?query=<запрос>&limit=10
    """
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("Формат: /search <город> <запрос>")
            return

        city = args[0]
        query = " ".join(args[1:])

        url = f"{API_BASE}/api/v1/index_search/city/{city}"
        params = {"query": query, "limit": 10}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                response = await resp.json()

        if response and response.get("status") == "success":
            results = response.get("results", [])
            total_found = response.get("total_found", 0)
            message_text = f"Найдено результатов: {total_found}\n"

            for idx, place in enumerate(results[:10], start=1):
                name = place.get("name", "???")
                address = place.get("address", "")
                score = place.get("score", 0)
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
    """
    Пример команды: /searchall park
    Делает GET-запрос:
    GET {API_BASE}/api/v1/index_search/all?query=<запрос>&limit=10
    """
    try:
        args = context.args
        if not args:
            await update.message.reply_text("Формат: /searchall <запрос>")
            return

        query = " ".join(args)
        url = f"{API_BASE}/api/v1/index_search/all"
        params = {"query": query, "limit": 10}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                response = await resp.json()

        if response and response.get("status") == "success":
            results = response.get("results", [])
            total_found = response.get("total_found", 0)
            message_text = f"Найдено результатов (по всем городам): {total_found}\n"
            for idx, place in enumerate(results[:10], start=1):
                city = place.get("city", "???")
                name = place.get("name", "???")
                address = place.get("address", "")
                score = place.get("score", 0)
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


# Семантический поиск
async def semantic_search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Пример команды: /semantic Москва интересный музей
    Делает GET-запрос:
    GET {API_BASE}/api/v1/semantic/city/{city}?query=<запрос>&limit=10
    """
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("Формат: /semantic <город> <запрос>")
            return

        city = args[0]
        query = " ".join(args[1:])
        url = f"{API_BASE}/api/v1/semantic/city/{city}"
        params = {"query": query, "limit": 10}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                response = await resp.json()

        if response and response.get("status") == "success":
            results = response.get("results", [])
            total_found = response.get("total_found", 0)
            message_text = f"Найдено результатов (семантический поиск): {total_found}\n"
            for idx, place in enumerate(results[:10], start=1):
                name = place.get("name", "???")
                address = place.get("address", "")
                score = place.get("score", 0)
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
        logger.exception("semantic_search_command error:")
        await update.message.reply_text("Произошла ошибка при семантическом поиске (см. логи).")

async def semantic_search_all_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Пример команды: /semanticall достопримечательности
    Делает GET-запрос:
    GET {API_BASE}/api/v1/semantic/all?query=<запрос>&limit=10
    """
    try:
        args = context.args
        if not args:
            await update.message.reply_text("Формат: /semanticall <запрос>")
            return

        query = " ".join(args)
        url = f"{API_BASE}/api/v1/semantic/all"
        params = {"query": query, "limit": 10}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                response = await resp.json()

        if response and response.get("status") == "success":
            results = response.get("results", [])
            total_found = response.get("total_found", 0)
            message_text = f"Найдено результатов (семантический поиск по всем городам): {total_found}\n"
            for idx, place in enumerate(results[:10], start=1):
                city = place.get("city", "???")
                name = place.get("name", "???")
                address = place.get("address", "")
                score = place.get("score", 0)
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
        logger.exception("semantic_search_all_command error:")
        await update.message.reply_text("Произошла ошибка при семантическом поиске (см. логи).")

async def startsearch_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Начинаем пошаговый поиск.\nВыберите город:")
    buttons = [[InlineKeyboardButton(city, callback_data=city)] for city in AVAILABLE_CITIES]
    markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("Выберите город:", reply_markup=markup)
    return ST_CITY

async def city_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    chosen_city = query.data
    context.user_data["chosen_city"] = chosen_city

    # Перейти сразу к запросу, без выбора типа места
    await query.edit_message_text(
        text=f"Вы выбрали город: {chosen_city}.\nВведите поисковый запрос (например, 'museum', 'cafe', 'park' и т.д.):"
    )
    return ST_QUERY

async def query_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_text = update.message.text
    context.user_data["search_query"] = user_text
    await run_inline_search(update, context)
    return ConversationHandler.END

async def run_inline_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = context.user_data.get("chosen_city")
    full_query = context.user_data.get("search_query", "").strip()

    # Пошаговый поиск использует индексный эндпоинт:
    url = f"{API_BASE}/api/v1/index_search/city/{city}"
    params = {"query": full_query, "limit": 10}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                response = await resp.json()

        if response and response.get("status") == "success":
            results = response.get("results", [])
            total_found = response.get("total_found", 0)
            msg = f"Готово! Найдено результатов: {total_found}\n"
            for idx, place in enumerate(results[:10], start=1):
                name = place.get("name", "???")
                address = place.get("address", "")
                score = place.get("score", 0)
                summary = place.get("summary", "")
                msg += (
                    f"\n<b>{idx}. {name}</b>\n"
                    f"Адрес: {address}\n"
                    f"Скор: {score:.2f}\n"
                    f"{summary}\n"
                )
            await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
        else:
            err_msg = response.get("message", "Ошибка") if response else "Неизвестная ошибка"
            await update.message.reply_text(f"Ошибка: {err_msg}")

    except Exception as e:
        logger.exception("run_inline_search error:")
        await update.message.reply_text("Произошла ошибка при поиске.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Поиск отменен.")
    return ConversationHandler.END


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    logger.debug(f"Пришло произвольное сообщение: {user_text!r}")
    await update.message.reply_text(
        "Я пока понимаю только /search, /searchall, /semantic, /semanticall и /startsearch.\n"
        "Попробуй /help для списка команд."
    )

def main():
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("startsearch", startsearch_command)],
        states={
            ST_CITY: [CallbackQueryHandler(city_chosen)],
            ST_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, query_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("searchall", search_all_command))
    application.add_handler(CommandHandler("semantic", semantic_search_command))
    application.add_handler(CommandHandler("semanticall", semantic_search_all_command))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    application.run_polling()
    logger.info("Bot started!")


if __name__ == "__main__":
    main()
