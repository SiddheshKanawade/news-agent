"""Test database functionality."""

from prazo.core.db import check_urls_exist, save_news_items, initialize_database
from prazo.schemas import NewsItem


def test_database_operations():
    """Test basic database operations."""
    # Initialize database
    initialize_database()
    
    # Create test items
    test_items = [
        NewsItem(
            title="Test Article 1 - Database Testing with MongoDB Integration",
            summary="This is a comprehensive test article to verify database functionality. " * 10,
            sources=["https://test-db-1.com/article1", "https://test-db-1.com/article2"],
            topic=["Testing", "Database"],
            groups=["Test Group"],
            tool_source=["tavily"],
            published_date="2025-10-22"
        ),
        NewsItem(
            title="Test Article 2 - URL Deduplication Feature Testing",
            summary="This is another test article to check URL deduplication feature. " * 10,
            sources=["https://test-db-2.com/article1"],
            topic=["Testing"],
            groups=["Test Group"],
            tool_source=["arxiv"],
            published_date="2025-10-22"
        ),
    ]
    
    print("\n=== Testing Database Functionality ===\n")
    
    # Test 1: Save items
    print("Test 1: Saving news items to database...")
    saved_count = save_news_items(test_items)
    print(f"✓ Saved {saved_count} items\n")
    
    # Test 2: Check existing URLs
    print("Test 2: Checking if URLs exist...")
    urls_to_check = [
        "https://test-db-1.com/article1",  # Should exist
        "https://test-db-1.com/article2",  # Should exist
        "https://test-db-3.com/article3",  # Should not exist
    ]
    existing_urls = check_urls_exist(urls_to_check)
    print(f"Checked URLs: {urls_to_check}")
    print(f"Existing URLs: {list(existing_urls)}")
    print(f"New URLs: {[url for url in urls_to_check if url not in existing_urls]}")
    
    assert "https://test-db-1.com/article1" in existing_urls
    assert "https://test-db-1.com/article2" in existing_urls
    assert "https://test-db-3.com/article3" not in existing_urls
    print("✓ URL checking works correctly\n")
    
    # Test 3: Check tool functionality
    print("Test 3: Testing database_check_tool...")
    from prazo.utils.tools import database_check_tool
    
    db_tool = database_check_tool()
    result = db_tool.invoke({
        "query": "https://test-db-1.com/article1, https://test-db-new.com/article"
    })
    
    print(f"Tool result:\n{result}")
    
    # Verify the result contains expected information
    assert "https://test-db-1.com/article1" in result
    assert "https://test-db-new.com/article" in result
    assert "Existing URLs" in result or "existing" in result.lower()
    assert "New URLs" in result or "new" in result.lower()
    print("✓ DB tool works correctly\n")
    
    print("=== All Tests Passed! ===\n")


if __name__ == "__main__":
    test_database_operations()

