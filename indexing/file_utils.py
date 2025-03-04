# utils/file_utils.py
import json
import re
import logging
from typing import Dict, Any

def save_json(data: Dict[str, Any], filename: str):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"[Save] Данные для '{data.get('place')}' сохранены в {filename}")
    except Exception as e:
        logging.error(f"[Save] Ошибка при сохранении данных в {filename}: {e}")
