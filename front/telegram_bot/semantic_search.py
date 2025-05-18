import logging
import aiohttp
from telegram.constants import ParseMode
from telegram import (
    Update,
)
from telegram.ext import (
    ContextTypes,
)

import sys, os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))
from src.configs.config import settings

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def semantic_search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Пример команды: /semantic Москва интересный музей
    Делает GET-запрос:
    GET {API_BASE}/semantic/city/{city}?query=<запрос>&limit=10
    """
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("Формат: /semantic <город> <запрос>")
            return

        city = args[0]
        query = " ".join(args[1:])
        url = f"{settings.API_BASE}/semantic/city/{city}"
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
        url = f"{settings.API_BASE}/semantic/all"
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