import json
import re
import logging
from typing import Dict, Any, List
from pymongo import MongoClient, errors
import logging

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


class MongoDBHandler:
    def __init__(self, uri: str, db_name: str, collection_name: str):
        self.uri = uri
        self.db_name = db_name
        self.collection_name = collection_name

    def __enter__(self):
        self.client = MongoClient(self.uri)
        self.db = self.client[self.db_name]
        self.collection = self.db[self.collection_name]
        return self.collection

    def __exit__(self, exc_type, exc_value, traceback):
        self.client.close()
        if exc_type:
            logging.error(f"An error occurred: {exc_value}")
        return True  # Suppress propagation of the exception

def save_json(data: List[Dict[str, Any]], filename: str, unique_field: str, uri: str, db_name: str, collection_name: str):
    try:
        with MongoDBHandler(uri, db_name, collection_name) as collection:
            # Создание индекса для уникального поля, если он еще не существует
            collection.create_index([(unique_field, 1)], unique=True)
            # Фильтрация данных, чтобы избежать дубликатов
            existing_values = {doc[unique_field] for doc in collection.find({}, {unique_field: 1})}
            new_data = [doc for doc in data if doc[unique_field] not in existing_values]
            if new_data:
                # Пакетная вставка новых документов
                result = collection.insert_many(new_data)
                logging.info(f"Inserted {len(result.inserted_ids)} new documents.")
            else:
                logging.info("No new documents to insert.")
    except errors.PyMongoError as e:
        logging.error(f"An error occurred while interacting with MongoDB: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")


def load_json(filename: str):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading JSON from {filename}: {e}")
        return None
