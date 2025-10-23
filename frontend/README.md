# News Agent Frontend

A simple, clean frontend for displaying news items collected by the News Agent.

## Features

- 📱 **Fully Responsive Design** - Works seamlessly on desktop, tablet, and mobile devices
- 🗂️ **Tab Navigation** - Switch between All News, Daily News, and Followed Topics
- 🔍 **Real-time Search** - Instant filtering by title, summary, topic, or group
- 🏷️ **Source Filters** - Filter by tool source (ArXiv, Tavily, Wikipedia, Reddit)
- 🎨 **Modern UI** - Beautiful gradient design with smooth animations and transitions
- 📖 **Modal Dialog** - Click "Read More" to view full article summary in a clean modal
- ✂️ **Smart Preview** - Cards show 30 words total (title + summary) for consistent sizing
- 📄 **Pagination** - Load more articles on demand (50 items per page)
- 🔄 **Refresh** - Easily reload latest news with one click
- 📊 **Live Stats** - Shows number of items displayed and available
- ⏱️ **Smart Sorting** - Sorted by publication date (most recent first)
- 🎯 **Deduplication** - Ensures unique news items based on source URLs

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

- `GET /api/news` - Get paginated news items (supports `?limit=50&offset=0&reset=false&category=all`)
  - Returns items sorted by publication date (most recent first)
  - Automatically deduplicates based on source URLs
  - Default limit: 50 items per request
  - Max limit: 100 items per request
  - Category options: 
    - `all` - All news items
    - `daily` - Items with tool_source='daily_news'
    - `topics` - Items where tool_source ≠ 'daily_news' (includes empty/missing tool_source)
  - Use `reset=true` to clear the deduplication cache (done automatically on page load)
- `GET /api/news/stats` - Get statistics about the collection
- `GET /api/health` - Health check endpoint (includes cache size)
- `POST /api/news/clear-cache` - Manually clear the deduplication cache

## Configuration

The API connects to MongoDB using the configuration from `prazo/core/config.py`. Make sure your MongoDB connection is properly configured there.

## Features in Detail

### Tab Navigation
Switch between different news categories:
- **🌐 All News** - All news items from all sources
- **📅 Daily News** - Breaking news and current events (tool_source: daily_news)
- **📚 Followed Topics** - Everything else (ArXiv, Wikipedia, Reddit, Tavily, and items with empty/missing tool_source)

### Search
Type in the search box to filter news by title, summary, topic, or group in real-time.

### Source Filters
Click on the filter buttons to show only news from specific sources:
- **All** - Show all news items
- **ArXiv** - Show only academic papers
- **Tavily** - Show only web news
- **Wikipedia** - Show only Wikipedia articles
- **Reddit** - Show only Reddit discussions

### News Cards
Each news card displays:
- **Title** - Article headline (may be truncated if very long)
- **Badges** - Color-coded tool source, topic, and group tags
- **Date** - Publication date (formatted as Month Day, Year)
- **Preview** - 30 words total from title + summary for consistent card sizing
- **Read More Button** - Opens full article in modal dialog

### Modal Dialog
Click "Read More" on any card to view:
- Full article title and metadata
- Complete summary (no truncation)
- All source links
- Publication date and time
- All topic and group tags
- Easy close with X button, Escape key, or clicking outside

### Pagination
- **Initial Load**: 50 articles for fast page performance
- **Load More**: Click button at bottom to load 50 more articles
- **Smart Loading**: Button shows "Loading..." state and disappears when all items loaded

### Smart Deduplication
The API automatically filters out duplicate news items based on source URLs:
- If two news items share any source URL, only the most recent one is shown
- Deduplication works across all pagination requests
- Cache is automatically reset when you refresh the page or use the refresh button
- This ensures you see only unique, high-quality news items

### Mobile Responsiveness
Fully optimized for mobile devices:
- **Tablet (768px)**: Adjusted layout with larger touch targets
- **Mobile (480px)**: Single column layout with optimized font sizes
- **Touch-friendly**: Large buttons and comfortable tap targets
- **Smooth Scrolling**: Optimized for touch gestures
- **Modal Adaptation**: Full-screen modal on small devices

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

