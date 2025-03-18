import json
import re
import logging
from typing import Dict, Any

def normalize_filename(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r'[\s-]+', '_', name)
    name = re.sub(r'[^\w_]', '', name)
    return name

def save_json(data: Dict[str, Any], filename: str):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"[Save] Data saved to {filename}")
    except Exception as e:
        logging.error(f"[Save] Error saving data to {filename}: {e}")


def load_json(filename: str):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading JSON from {filename}: {e}")
        return None
