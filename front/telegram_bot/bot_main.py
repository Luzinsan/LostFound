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

import sys, os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))
from src.configs.config import settings
from front.telegram_bot.index_search import search_command, search_all_command
from front.telegram_bot.semantic_search import semantic_search_command, semantic_search_all_command


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

ST_CITY = 1
ST_TYPE = 2
ST_QUERY = 3
 

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


async def startsearch_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Начинаем пошаговый поиск.\nВыберите город:")
    buttons = [[InlineKeyboardButton(city, callback_data=city)] for city in settings.CITIES]
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
    url = f"{settings.API_BASE}/api/v1/index_search/city/{city}"
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
        .token(settings.TELEGRAM_BOT_API)
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
