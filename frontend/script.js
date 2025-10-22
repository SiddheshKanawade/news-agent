let allNewsItems = [];
let filteredNewsItems = [];
let currentOffset = 0;
let isLoading = false;
let hasMore = true;
let totalItems = 0;

// API Configuration
const API_URL = 'http://localhost:8000/api/news';
const ITEMS_PER_PAGE = 50;

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    loadNewsItems(true);
    setupEventListeners();
    setupInfiniteScroll();
});

// Setup event listeners
function setupEventListeners() {
    // Search functionality
    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('input', (e) => {
        filterAndDisplayNews();
    });

    // Filter buttons
    const filterButtons = document.querySelectorAll('.filter-btn');
    filterButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            filterButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filterAndDisplayNews();
        });
    });

    // Refresh button
    const refreshBtn = document.getElementById('refreshBtn');
    refreshBtn.addEventListener('click', () => {
        // Reset pagination state
        allNewsItems = [];
        currentOffset = 0;
        hasMore = true;
        document.getElementById('newsContainer').innerHTML = '';
        loadNewsItems(true);
    });
}

// Setup infinite scroll
function setupInfiniteScroll() {
    window.addEventListener('scroll', () => {
        // Check if user has scrolled near the bottom
        const scrollHeight = document.documentElement.scrollHeight;
        const scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
        const clientHeight = document.documentElement.clientHeight;

        // Load more when user is 500px from bottom
        if (scrollHeight - scrollTop - clientHeight < 500) {
            if (!isLoading && hasMore) {
                loadNewsItems(false);
            }
        }
    });
}

// Load news items from API with pagination
async function loadNewsItems(isInitialLoad = false) {
    if (isLoading || (!hasMore && !isInitialLoad)) {
        return;
    }

    isLoading = true;
    const loadingDiv = document.getElementById('loading');
    const errorDiv = document.getElementById('error');
    const newsContainer = document.getElementById('newsContainer');

    if (isInitialLoad) {
        loadingDiv.style.display = 'block';
        errorDiv.style.display = 'none';
        newsContainer.innerHTML = '';
    } else {
        // Show loading indicator at bottom for infinite scroll
        const loadingIndicator = document.createElement('div');
        loadingIndicator.id = 'loadingMore';
        loadingIndicator.className = 'loading';
        loadingIndicator.textContent = 'Loading more news...';
        loadingIndicator.style.gridColumn = '1/-1';
        newsContainer.appendChild(loadingIndicator);
    }

    try {
        const url = `${API_URL}?limit=${ITEMS_PER_PAGE}&offset=${currentOffset}`;
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        const newItems = data.news_items || [];

        // Append new items to existing ones
        allNewsItems = [...allNewsItems, ...newItems];

        // Update pagination state
        currentOffset += newItems.length;
        hasMore = data.has_more || false;
        totalItems = data.total || allNewsItems.length;

        // Filter and display
        filterAndDisplayNews();
        updateStats();

        if (isInitialLoad) {
            loadingDiv.style.display = 'none';
        } else {
            // Remove loading indicator
            const loadingIndicator = document.getElementById('loadingMore');
            if (loadingIndicator) {
                loadingIndicator.remove();
            }
        }
    } catch (error) {
        console.error('Error loading news:', error);

        if (isInitialLoad) {
            loadingDiv.style.display = 'none';
            errorDiv.style.display = 'block';
            errorDiv.textContent = `Failed to load news items: ${error.message}. Make sure the API server is running on ${API_URL}`;
        } else {
            // Remove loading indicator and show error
            const loadingIndicator = document.getElementById('loadingMore');
            if (loadingIndicator) {
                loadingIndicator.remove();
            }
        }
    } finally {
        isLoading = false;
    }
}

// Filter and display news based on search and filter criteria
function filterAndDisplayNews() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const activeFilter = document.querySelector('.filter-btn.active').dataset.filter;

    filteredNewsItems = allNewsItems.filter(item => {
        // Apply tool source filter
        let toolMatch = true;
        if (activeFilter !== 'all') {
            toolMatch = item.tool_source && item.tool_source.some(
                tool => tool.toLowerCase() === activeFilter.toLowerCase()
            );
        }

        // Apply search filter
        let searchMatch = true;
        if (searchTerm) {
            searchMatch =
                item.title.toLowerCase().includes(searchTerm) ||
                item.summary.toLowerCase().includes(searchTerm) ||
                (item.topic && item.topic.some(t => t.toLowerCase().includes(searchTerm))) ||
                (item.groups && item.groups.some(g => g.toLowerCase().includes(searchTerm)));
        }

        return toolMatch && searchMatch;
    });

    displayNewsItems(filteredNewsItems);
    updateStats();
}

// Display news items in the container
function displayNewsItems(items) {
    const newsContainer = document.getElementById('newsContainer');
    newsContainer.innerHTML = '';

    if (items.length === 0) {
        newsContainer.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 40px; background: white; border-radius: 12px;">
                <h3 style="color: #667eea;">No news items found</h3>
                <p style="color: #888; margin-top: 10px;">Try adjusting your filters or search terms</p>
            </div>
        `;
        return;
    }

    items.forEach(item => {
        const card = createNewsCard(item);
        newsContainer.appendChild(card);
    });
}

// Create a news card element
function createNewsCard(item) {
    const card = document.createElement('div');
    card.className = 'news-card';

    // Format date
    const publishedDate = item.published_date
        ? new Date(item.published_date).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        })
        : 'Date not available';

    // Create tool source badges
    const toolBadges = (item.tool_source || []).map(tool =>
        `<span class="badge ${tool.toLowerCase()}">${tool}</span>`
    ).join('');

    // Create topic badges
    const topicBadges = (item.topic || []).slice(0, 2).map(topic =>
        `<span class="badge topic">${topic}</span>`
    ).join('');

    // Create group badges
    const groupBadges = (item.groups || []).slice(0, 2).map(group =>
        `<span class="badge group">${group}</span>`
    ).join('');

    // Create source links
    const sourceLinks = (item.sources || []).map((source, idx) =>
        `<a href="${source}" target="_blank" class="source-link" title="${source}">
            📄 Source ${idx + 1}
        </a>`
    ).join('');

    card.innerHTML = `
        <h2>${item.title}</h2>
        <div class="news-meta">
            ${toolBadges}
            ${topicBadges}
            ${groupBadges}
        </div>
        <div class="news-date">📅 ${publishedDate}</div>
        <div class="news-summary">${item.summary}</div>
        ${sourceLinks ? `
            <div class="news-sources">
                <h4>Sources</h4>
                <div class="source-links">
                    ${sourceLinks}
                </div>
            </div>
        ` : ''}
    `;

    return card;
}

// Update statistics
function updateStats() {
    const statsDiv = document.getElementById('stats');
    const loadedItems = allNewsItems.length;
    const displayedItems = filteredNewsItems.length;

    if (loadedItems === 0) {
        statsDiv.textContent = 'No news items available';
    } else {
        let statsText = '';
        if (loadedItems === displayedItems) {
            statsText = `Showing ${loadedItems}`;
        } else {
            statsText = `Showing ${displayedItems} of ${loadedItems}`;
        }

        // Add total if we know it and it's different from loaded
        if (totalItems > loadedItems) {
            statsText += ` (${totalItems} total)`;
        }

        statsText += ' news items';

        // Add scroll hint if there are more to load
        if (hasMore) {
            statsText += ' • Scroll down to load more';
        }

        statsDiv.textContent = statsText;
    }
}

