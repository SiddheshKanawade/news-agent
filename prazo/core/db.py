from typing import List, Set

import pymongo

from prazo.core.config import config
from prazo.core.logger import logger
from prazo.schemas import NewsItem

# Initialize MongoDB connection
client = pymongo.MongoClient(config.MONGODB_URI)
db = client[config.MONGODB_DB]
collection = db[config.MONGODB_COLLECTION]


def save_news_items(news_items: List[NewsItem]) -> int:
    """
    Save multiple news items to the database.
    
    Args:
        news_items: List of NewsItem objects to save
        
    Returns:
        int: Number of items successfully inserted
    """
    if not news_items:
        logger.info("No news items to save")
        return 0
    
    try:
        # Convert NewsItem objects to dictionaries
        items_to_insert = [item.model_dump() for item in news_items]
        result = collection.insert_many(items_to_insert)
        count = len(result.inserted_ids)
        logger.info(f"Successfully saved {count} news items to database")
        return count
    except Exception as e:
        logger.error(f"Error saving news items to database: {e}")
        return 0


def check_urls_exist(urls: List[str]) -> Set[str]:
    """
    Check which URLs from the provided list already exist in the database.
    
    Args:
        urls: List of URLs to check
        
    Returns:
        Set[str]: Set of URLs that exist in the database
    """
    if not urls:
        return set()
    
    try:
        # Find all documents where sources array contains any of the provided URLs
        existing_docs = collection.find(
            {"sources": {"$in": urls}},
            {"sources": 1, "_id": 0}
        )
        
        # Flatten all sources from found documents into a set
        existing_urls = set()
        for doc in existing_docs:
            existing_urls.update(doc.get("sources", []))
        
        # Return only the URLs from our input list that exist
        return existing_urls.intersection(set(urls))
    except Exception as e:
        logger.error(f"Error checking URLs in database: {e}")
        return set()


def get_all_existing_urls() -> Set[str]:
    """
    Get all unique URLs that exist in the database.
    
    Returns:
        Set[str]: Set of all existing URLs
    """
    try:
        # Get all sources from all documents
        existing_docs = collection.find({}, {"sources": 1, "_id": 0})
        
        all_urls = set()
        for doc in existing_docs:
            all_urls.update(doc.get("sources", []))
        
        logger.info(f"Found {len(all_urls)} unique URLs in database")
        return all_urls
    except Exception as e:
        logger.error(f"Error getting all URLs from database: {e}")
        return set()


def initialize_database():
    """
    Initialize the database by creating necessary indexes.
    Should be called once at application startup.
    """
    try:
        # Create index on sources field for faster URL lookups
        collection.create_index("sources")
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating database indexes: {e}")