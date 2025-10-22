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

# Global cache to track seen URLs for deduplication across pagination
# This gets reset when the server restarts or can be manually cleared
seen_urls_cache = set()


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


def deduplicate_by_sources(news_items: List[dict]) -> List[dict]:
    """
    Deduplicate news items based on source URLs.
    If two news items share any source URL, keep only the most recent one.
    
    Args:
        news_items: List of news item dictionaries (already sorted by date)
    
    Returns:
        List of unique news items
    """
    if not news_items:
        return []
    
    seen_urls = set()
    unique_items = []
    
    for item in news_items:
        sources = item.get('sources', [])
        
        # Check if any source URL has been seen before
        has_duplicate = any(url in seen_urls for url in sources)
        
        if not has_duplicate:
            # This is a unique item, add all its sources to seen_urls
            seen_urls.update(sources)
            unique_items.append(item)
    
    logger.info(f"Deduplicated {len(news_items)} items to {len(unique_items)} unique items")
    return unique_items


@app.route('/api/news', methods=['GET'])
def get_news():
    """Get paginated news items from the database, sorted by time and deduplicated"""
    global seen_urls_cache
    
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
        reset_cache = request.args.get('reset', 'false').lower() == 'true'
        
        # Limit max items per request to prevent abuse
        limit = min(limit, 100)
        
        # Reset cache if requested (e.g., on page refresh)
        if reset_cache or offset == 0:
            seen_urls_cache = set()
            logger.info("Reset deduplication cache")
        
        # To handle deduplication properly with pagination, we need to:
        # 1. Fetch more items than requested to account for duplicates
        # 2. Deduplicate them against global seen URLs
        # 3. Return only the requested number
        
        # Fetch extra items to account for potential duplicates
        # We'll fetch up to 3x the limit to ensure we get enough unique items
        fetch_limit = limit * 3
        unique_items = []
        current_offset = offset
        
        # Keep fetching until we have enough unique items or run out of data
        while len(unique_items) < limit:
            # Fetch a batch of news items sorted by published_date (most recent first)
            news_items = list(
                collection.find({})
                .sort([
                    ('published_date', pymongo.DESCENDING),
                    ('created_at', pymongo.DESCENDING)  # Fallback sort
                ])
                .skip(current_offset)
                .limit(fetch_limit)
            )
            
            if not news_items:
                # No more items in database
                break
            
            # Filter out items that we've already seen
            for item in news_items:
                sources = item.get('sources', [])
                
                # Check if any source URL has been seen before
                has_duplicate = any(url in seen_urls_cache for url in sources)
                
                if not has_duplicate and len(unique_items) < limit:
                    # This is a unique item, add it and track its sources
                    seen_urls_cache.update(sources)
                    unique_items.append(item)
            
            # If we didn't get any new unique items, try fetching more from next batch
            if len(unique_items) < limit and len(news_items) == fetch_limit:
                current_offset += fetch_limit
            else:
                break
        
        # Serialize and prepare response
        serialized_items = [serialize_news_item(item) for item in unique_items]
        
        # Get total count
        total_count = collection.count_documents({})
        
        # Calculate if there are more items
        has_more = current_offset + len(news_items) < total_count
        
        logger.info(f"Retrieved {len(serialized_items)} unique news items (offset: {offset}, limit: {limit}, cached URLs: {len(seen_urls_cache)})")
        
        return jsonify({
            'count': len(serialized_items),
            'total': total_count,
            'offset': offset,
            'limit': limit,
            'has_more': has_more,
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
        'database': db_status,
        'cached_urls': len(seen_urls_cache)
    })


@app.route('/api/news/clear-cache', methods=['POST'])
def clear_cache():
    """Clear the deduplication cache"""
    global seen_urls_cache
    old_size = len(seen_urls_cache)
    seen_urls_cache = set()
    logger.info(f"Cleared deduplication cache (was {old_size} URLs)")
    return jsonify({
        'status': 'ok',
        'message': f'Cache cleared ({old_size} URLs removed)'
    })


if __name__ == '__main__':
    print("Starting News Agent API Server...")
    print(f"API will be available at: http://localhost:8000")
    print(f"Connected to MongoDB: {config.MONGODB_URI}")
    print(f"Database: {config.MONGODB_DB}, Collection: {config.MONGODB_COLLECTION}")
    app.run(host='0.0.0.0', port=8000, debug=True)

