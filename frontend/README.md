# News Agent Frontend

A simple, clean frontend for displaying news items collected by the News Agent.

## Features

- 📱 Responsive design that works on all devices
- 🔍 Real-time search functionality
- 🏷️ Filter by tool source (ArXiv, Tavily, Wikipedia, Reddit)
- 🎨 Beautiful gradient UI with smooth animations
- 🔄 Refresh button to reload latest news
- 📊 Stats display showing number of items
- ⏱️ Sorted by publication date (most recent first)
- ∞ Infinite scroll - loads 50 items at a time for better performance
- 🎯 Smart deduplication - ensures unique news items based on source URLs

## Setup & Usage

### 1. Start the API Server

First, make sure you have Flask and Flask-CORS installed:

```bash
pip install flask flask-cors
```

Then start the API server:

```bash
python frontend/api.py
```

The API will be available at `http://localhost:8000`

### 2. Open the Frontend

Simply open `frontend/index.html` in your web browser:

```bash
# On macOS
open frontend/index.html

# On Linux
xdg-open frontend/index.html

# Or just double-click the index.html file
```

### 3. Alternative: Serve with Python HTTP Server

For a better development experience, you can serve the frontend using Python's built-in HTTP server:

```bash
# In one terminal, start the API
python frontend/api.py

# In another terminal, serve the frontend
cd frontend
python -m http.server 3000
```

Then open `http://localhost:3000` in your browser.

## File Structure

```
frontend/
├── index.html   # Main HTML page
├── style.css    # Styling and layout
├── script.js    # Frontend logic and API calls
├── api.py       # Flask API server to fetch data from MongoDB
└── README.md    # This file
```

## API Endpoints

- `GET /api/news` - Get paginated news items (supports `?limit=50&offset=0&reset=false`)
  - Returns items sorted by publication date (most recent first)
  - Automatically deduplicates based on source URLs
  - Default limit: 50 items per request
  - Max limit: 100 items per request
  - Use `reset=true` to clear the deduplication cache (done automatically on page load)
- `GET /api/news/stats` - Get statistics about the collection
- `GET /api/health` - Health check endpoint (includes cache size)
- `POST /api/news/clear-cache` - Manually clear the deduplication cache

## Configuration

The API connects to MongoDB using the configuration from `prazo/core/config.py`. Make sure your MongoDB connection is properly configured there.

## Features in Detail

### Search
Type in the search box to filter news by title, summary, topic, or group.

### Filters
Click on the filter buttons to show only news from specific sources:
- **All** - Show all news items
- **ArXiv** - Show only academic papers
- **Tavily** - Show only web news
- **Wikipedia** - Show only Wikipedia articles
- **Reddit** - Show only Reddit discussions

### News Cards
Each news card displays:
- Title
- Tool source badges (colored indicators)
- Topic and group tags
- Publication date (sorted newest first)
- Summary
- Links to original sources

### Infinite Scroll
The frontend loads only 50 articles initially for fast page load. As you scroll down, it automatically loads more articles in batches of 50. This provides a smooth browsing experience even with thousands of news items.

### Smart Deduplication
The API automatically filters out duplicate news items based on source URLs:
- If two news items share any source URL, only the most recent one is shown
- Deduplication works across all pagination requests
- Cache is automatically reset when you refresh the page or use the refresh button
- This ensures you see only unique, high-quality news items

## Browser Compatibility

Works on all modern browsers:
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers

## Troubleshooting

**Problem**: "Failed to load news items" error

**Solution**: Make sure:
1. The API server is running (`python frontend/api.py`)
2. MongoDB is accessible with the credentials in your config
3. The collection has data (run the main agent to collect news)

**Problem**: CORS errors

**Solution**: The API includes CORS support. If you still see CORS errors, make sure you're accessing the frontend through a proper HTTP server (not `file://` protocol).

