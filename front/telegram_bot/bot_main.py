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

TELEGRAM_BOT_TOKEN = ""

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

ST_CITY = 1
ST_TYPE = 2
ST_QUERY = 3

AVAILABLE_CITIES = ["Москва", "Санкт-Петербург", "Нижний Новгород"]
AVAILABLE_TYPES = [
    "restaurant", "cafe", "tourist_attraction", "museum", "performing_arts_theater",
    "historical_place", "art_gallery", "park", "lodging", "church"
]

API_BASE = ""


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
        "Пример: /search Москва museum"
    )


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("Формат: /search <город> <запрос>")
            return

        city = args[0]
        query = " ".join(args[1:])

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_BASE}/index_search/city/{city}", params={"query": query, "limit": 10}) as resp:
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
    try:
        args = context.args
        if not args:
            await update.message.reply_text("Формат: /searchall <запрос>")
            return

        query = " ".join(args)

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_BASE}/index_search/all", params={"query": query, "limit": 10}) as resp:
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

    buttons = []
    row = []
    for i, place_type in enumerate(AVAILABLE_TYPES, start=1):
        row.append(InlineKeyboardButton(place_type, callback_data=place_type))
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
    user_text = update.message.text
    context.user_data["additional_query"] = user_text
    await run_inline_search(update, context)
    return ConversationHandler.END


async def skip_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["additional_query"] = ""
    await run_inline_search(update, context)
    return ConversationHandler.END


async def run_inline_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = context.user_data.get("chosen_city")
    place_type = context.user_data.get("chosen_type")
    additional = context.user_data.get("additional_query", "")
    full_query = f"{place_type} {additional}".strip()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_BASE}/index_search/city/{city}", params={"query": full_query, "limit": 10}) as resp:
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
        "Я пока понимаю только /search, /searchall, /startsearch.\n"
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
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    application.run_polling()
    logger.info("Bot started!")


if __name__ == "__main__":
    main()
