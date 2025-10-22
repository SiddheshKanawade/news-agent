"""
Simple Flask API to serve news items from MongoDB
"""

from datetime import datetime
from typing import List

import pymongo
from flask import Flask, jsonify
from flask_cors import CORS

# Import config from prazo
import sys
from pathlib import Path

# Add parent directory to path to import prazo
sys.path.append(str(Path(__file__).parent.parent))

from prazo.core.config import config
from prazo.core.logger import logger

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize MongoDB connection
try:
    client = pymongo.MongoClient(config.MONGODB_URI)
    db = client[config.MONGODB_DB]
    collection = db[config.MONGODB_COLLECTION]
    logger.info("Connected to MongoDB successfully")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    client = None
    db = None
    collection = None


def serialize_news_item(item: dict) -> dict:
    """Serialize a news item for JSON response"""
    # Convert datetime objects to ISO format strings
    if isinstance(item.get('published_date'), datetime):
        item['published_date'] = item['published_date'].isoformat()
    if isinstance(item.get('created_at'), datetime):
        item['created_at'] = item['created_at'].isoformat()
    if isinstance(item.get('updated_at'), datetime):
        item['updated_at'] = item['updated_at'].isoformat()
    
    # Remove MongoDB _id field
    if '_id' in item:
        del item['_id']
    
    return item


@app.route('/api/news', methods=['GET'])
def get_news():
    """Get paginated news items from the database, sorted by time"""
    try:
        if collection is None:
            return jsonify({
                'error': 'Database connection not available',
                'news_items': []
            }), 500
        
        # Get pagination parameters
        from flask import request
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Limit max items per request to prevent abuse
        limit = min(limit, 100)
        
        # Get total count
        total_count = collection.count_documents({})
        
        # Fetch news items with pagination, sorted by published_date (most recent first)
        # Sort in MongoDB for better performance
        news_items = list(
            collection.find({})
            .sort([
                ('published_date', pymongo.DESCENDING),
                ('created_at', pymongo.DESCENDING)  # Fallback sort
            ])
            .skip(offset)
            .limit(limit)
        )
        
        # Serialize and prepare response
        serialized_items = [serialize_news_item(item) for item in news_items]
        
        logger.info(f"Retrieved {len(serialized_items)} news items (offset: {offset}, limit: {limit})")
        
        return jsonify({
            'count': len(serialized_items),
            'total': total_count,
            'offset': offset,
            'limit': limit,
            'has_more': (offset + len(serialized_items)) < total_count,
            'news_items': serialized_items
        })
        
    except Exception as e:
        logger.error(f"Error fetching news items: {e}")
        return jsonify({
            'error': str(e),
            'news_items': []
        }), 500


@app.route('/api/news/stats', methods=['GET'])
def get_stats():
    """Get statistics about the news collection"""
    try:
        if collection is None:
            return jsonify({'error': 'Database connection not available'}), 500
        
        total_items = collection.count_documents({})
        
        # Get counts by tool source
        tool_sources = collection.aggregate([
            {'$unwind': '$tool_source'},
            {'$group': {'_id': '$tool_source', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ])
        
        # Get counts by topic
        topics = collection.aggregate([
            {'$unwind': '$topic'},
            {'$group': {'_id': '$topic', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ])
        
        return jsonify({
            'total_items': total_items,
            'by_tool_source': list(tool_sources),
            'top_topics': list(topics)
        })
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    db_status = 'connected' if collection is not None else 'disconnected'
    return jsonify({
        'status': 'ok',
        'database': db_status
    })


if __name__ == '__main__':
    print("Starting News Agent API Server...")
    print(f"API will be available at: http://localhost:8000")
    print(f"Connected to MongoDB: {config.MONGODB_URI}")
    print(f"Database: {config.MONGODB_DB}, Collection: {config.MONGODB_COLLECTION}")
    app.run(host='0.0.0.0', port=8000, debug=True)

