import pymongo

from prazo.core.config import config

client = pymongo.MongoClient(config.MONGODB_URI)
db = client[config.MONGODB_DB]
collection = db[config.MONGODB_COLLECTION]

def insert_news_item(news_item: NewsItem):
    collection.insert_one(news_item.model_dump())

def get_news_items():
    return collection.find()