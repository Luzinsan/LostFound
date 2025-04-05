import logging
from typing import Any, Dict, List, Union
from pymongo import MongoClient, errors, UpdateOne
from pymongo.collection import Collection
from config import settings

class MongoDBManager:
    """
    Class to manage MongoDB operations.

    This manager handles two collections:
      - 'cities' for aggregated Wikipedia data about cities and links to places.
      - 'places' for data retrieved from Google Places.
    The manager provides methods to save and load data for each collection.
    """

    def __init__(self, 
                 uri: str = settings.MONGO_URI, 
                 db_name: str = settings.MONGO_DB_NAME):
        """
        Initializes the MongoDBManager with the provided URI and database name.
        """
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collections = {
            "cities": {
                "collection": self.db["cities"], 
                "index": "city"},
            "places": {
                "collection": self.db["places"], 
                "index": "_id"},
            "city_indices": {
                "collection": self.db["city_indices"], 
                "index": "_id"},
        }
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        """
        Creates unique indexes to prevent duplicates in the collections.
        """
        try:
            for _, propertises in self.collections.items():
                if propertises["index"] != "_id":
                    propertises['collection'].create_index(propertises["index"], unique=True, background=True)
            logging.info("Unique indexes created successfully.")
        except errors.PyMongoError as e:
            logging.error(f"Error creating indexes: {e}")

    def save(self, 
             data: Union[Dict[str, Any], List[Dict[str, Any]]], 
             collection_name: str) -> None:
        """
        Saves or updates data in the specified collection.

        Args:
            data: A dictionary or list of dictionaries containing the data to save.
            collection_name: The name of the collection to save the data in.

        Raises:
            ValueError: If an invalid collection name is provided.
        """
        if collection_name not in self.collections:
            raise ValueError(f"Invalid collection name: {collection_name}")

        collection = self.collections[collection_name]['collection']

        if isinstance(data, dict):
            self._save_single(data, collection)
        elif isinstance(data, list):
            self._save_bulk(data, collection)
        else:
            raise TypeError("Data must be a dictionary or a list of dictionaries.")

    def _save_single(self, 
                     document: Dict[str, Any], 
                     collection: Collection) -> None:
        """
        Saves or updates a single document in the collection.

        Args:
            document: A dictionary containing the data to save.
            collection: The MongoDB collection to save the data in.
        """
        unique_field = self._get_unique_field(collection.name)
        filter_criteria = {unique_field: document[unique_field]}
        try:
            collection.replace_one(filter_criteria, document, upsert=True)
            logging.info(f"Document with {unique_field}='{document[unique_field]}' saved successfully.")
        except errors.PyMongoError as e:
            logging.error(f"Error saving document: {e}")

    def _save_bulk(self, documents: List[Dict[str, Any]], collection: Collection) -> None:
        """
        Bulk saves or updates multiple documents in the collection.

        Args:
            documents: A list of dictionaries containing the data to save.
            collection: The MongoDB collection to save the data in.
        """
        unique_field = self._get_unique_field(collection.name)
        operations = []
        for doc in documents:
            filter_criteria = {unique_field: doc[unique_field]}
            operations.append(UpdateOne(filter_criteria, {"$set": doc}, upsert=True))
        if operations:
            try:
                result = collection.bulk_write(operations)
                logging.info(f"Bulk operation completed. Inserted: {result.upserted_count}, updated: {result.modified_count}.")
            except errors.BulkWriteError as e:
                logging.error(f"Error during bulk insert: {e.details}")
            except errors.PyMongoError as e:
                logging.error(f"Error during bulk operation: {e}")

    def update_city_places(self, city: str, new_places: List[str]) -> None:
        """
        Updates the city document by adding new place references (place IDs) to the 'places' field.
        Uses $addToSet to avoid duplicates.

        Args:
            city: The name of the city.
            new_places: A list of new place IDs to add.
        """
        try:
            self.collections["cities"]['collection'].update_one(
                {"city": city},
                {"$addToSet": {"places": {"$each": new_places}}},
                upsert=True
            )
            logging.info(f"City document for '{city}' updated with new place references.")
        except errors.PyMongoError as e:
            logging.error(f"Error updating city places for '{city}': {e}")


    def _get_unique_field(self, collection_name: str) -> str:
        """
        Returns the name of the unique field for the given collection.

        Args:
            collection_name: The name of the collection.

        Returns:
            The name of the unique field.
        """
        if (propertises := self.collections.get(collection_name)):
            return propertises["index"]
        else:
            raise ValueError(f"Unknown collection: {collection_name}")

    def load(self, query: Dict[str, Any], collection_name: str) -> List[Dict[str, Any]]:
        """
        Loads data from the specified collection based on the given query.

        Args:
            query: A dictionary containing the query criteria.
            collection_name: The name of the collection to load data from.

        Returns:
            A list of dictionaries containing the query results.
        """
        if collection_name not in self.collections:
            raise ValueError(f"Invalid collection name: {collection_name}")

        collection = self.collections[collection_name]['collection']
        try:
            results = list(collection.find(query))
            logging.info(f"Loaded {len(results)} documents from collection '{collection_name}'.")
            return results
        except errors.PyMongoError as e:
            logging.error(f"Error loading data: {e}")
            return []

    def load_paginated(self, query: Dict[str, Any], collection_name: str, skip: int = 0, limit: int = 10) -> Dict[str, Any]:
        """
        Loads paginated data from the specified collection based on the given query.

        Args:
            query: A dictionary containing the query criteria.
            collection_name: The name of the collection to load data from.
            skip: Number of documents to skip.
            limit: Maximum number of documents to return.

        Returns:
            A dictionary containing the paginated results and total count.
        """
        if collection_name not in self.collections:
            raise ValueError(f"Invalid collection name: {collection_name}")

        collection = self.collections[collection_name]['collection']
        try:
            # Get total count
            total = collection.count_documents(query)
            
            # Get paginated results
            results = list(collection.find(query).skip(skip).limit(limit))
            
            logging.info(f"Loaded {len(results)} documents (page) from collection '{collection_name}'.")
            return {
                "results": results,
                "total": total
            }
        except errors.PyMongoError as e:
            logging.error(f"Error loading paginated data: {e}")
            return {
                "results": [],
                "total": 0
            }

    def close(self) -> None:
        """
        Closes the connection to MongoDB.
        """
        self.client.close()
        logging.info("Connection to MongoDB closed.")

mongo_manager = MongoDBManager()
