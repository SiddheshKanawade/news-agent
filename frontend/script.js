let allNewsItems = [];
let filteredNewsItems = [];
let currentOffset = 0;
let isLoading = false;
let hasMore = true;
let totalItems = 0;
let currentCategory = 'all';

// API Configuration
const API_URL = 'http://localhost:8000/api/news';
const ITEMS_PER_PAGE = 50;

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    loadNewsItems(true);
    setupEventListeners();
    setupModalHandlers();
});

// Setup event listeners
function setupEventListeners() {
    // Tab buttons
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            tabButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentCategory = btn.dataset.category;
            resetAndLoadNews();
        });
    });

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
        resetAndLoadNews();
    });

    // Load more button
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    loadMoreBtn.addEventListener('click', () => {
        loadNewsItems(false);
    });
}

// Reset state and load news
function resetAndLoadNews() {
    allNewsItems = [];
    currentOffset = 0;
    hasMore = true;
    document.getElementById('newsContainer').innerHTML = '';
    loadNewsItems(true);
}

// Setup modal handlers
function setupModalHandlers() {
    const modal = document.getElementById('articleModal');
    const modalClose = document.getElementById('modalClose');

    // Close modal when clicking X button
    modalClose.addEventListener('click', () => {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    });

    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    });

    // Close modal with Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.style.display === 'block') {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    });
}

// Open modal with article details
function openArticleModal(item) {
    const modal = document.getElementById('articleModal');
    const modalBody = document.getElementById('modalBody');

    // Format date
    const publishedDate = item.published_date
        ? new Date(item.published_date).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        })
        : 'Date not available';

    // Create tool source badges
    const toolBadges = (item.tool_source || []).map(tool =>
        `<span class="badge ${tool.toLowerCase()}">${tool}</span>`
    ).join('');

    // Create topic badges
    const topicBadges = (item.topic || []).map(topic =>
        `<span class="badge topic">${topic}</span>`
    ).join('');

    // Create group badges
    const groupBadges = (item.groups || []).map(group =>
        `<span class="badge group">${group}</span>`
    ).join('');

    // Create source links
    const sourceLinks = (item.sources || []).map((source, idx) =>
        `<a href="${source}" target="_blank" class="source-link" title="${source}">
            📄 Source ${idx + 1}
        </a>`
    ).join('');

    modalBody.innerHTML = `
        <h2 class="modal-title">${item.title}</h2>
        <div class="modal-meta">
            <div class="modal-date">📅 ${publishedDate}</div>
            <div class="modal-badges">
                ${toolBadges}
                ${topicBadges}
                ${groupBadges}
            </div>
        </div>
        <div class="modal-summary">${item.summary}</div>
        ${sourceLinks ? `
            <div class="modal-sources">
                <h4>Sources</h4>
                <div class="source-links">
                    ${sourceLinks}
                </div>
            </div>
        ` : ''}
    `;

    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
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
    }

    try {
        // Add reset parameter for initial load to clear the deduplication cache
        const resetParam = isInitialLoad ? '&reset=true' : '';
        const url = `${API_URL}?limit=${ITEMS_PER_PAGE}&offset=${currentOffset}&category=${currentCategory}${resetParam}`;
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
        updatePaginationControls();

        if (isInitialLoad) {
            loadingDiv.style.display = 'none';
        }
    } catch (error) {
        console.error('Error loading news:', error);

        if (isInitialLoad) {
            loadingDiv.style.display = 'none';
            errorDiv.style.display = 'block';
            errorDiv.textContent = `Failed to load news items: ${error.message}. Make sure the API server is running on ${API_URL}`;
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

// Truncate text to first N words
function truncateText(text, wordLimit) {
    const words = text.split(' ');
    if (words.length <= wordLimit) {
        return text;
    }
    return words.slice(0, wordLimit).join(' ') + '...';
}

// Truncate title and summary combined to N words total
function truncateTitleAndSummary(title, summary, totalWordLimit) {
    const combinedText = title + ' ' + summary;
    const words = combinedText.split(' ');

    if (words.length <= totalWordLimit) {
        return { title, summary };
    }

    // Calculate how many words to use from title and summary
    const titleWords = title.split(' ');
    const titleWordCount = titleWords.length;

    if (titleWordCount >= totalWordLimit) {
        // If title alone exceeds limit, truncate title only
        return {
            title: truncateText(title, totalWordLimit),
            summary: ''
        };
    }

    // Use full title and truncate summary
    const remainingWords = totalWordLimit - titleWordCount;
    return {
        title: title,
        summary: truncateText(summary, remainingWords)
    };
}

// Create a news card element
function createNewsCard(item) {
    const card = document.createElement('div');
    card.className = 'news-card';

    // Format date
    const publishedDate = item.published_date
        ? new Date(item.published_date).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
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

    // Truncate title + summary to 30 words total for consistent card size
    const truncated = truncateTitleAndSummary(item.title, item.summary, 30);
    const displayTitle = truncated.title;
    const displaySummary = truncated.summary;

    card.innerHTML = `
        <h2>${displayTitle}</h2>
        <div class="news-meta">
            ${toolBadges}
            ${topicBadges}
            ${groupBadges}
        </div>
        <div class="news-date">📅 ${publishedDate}</div>
        ${displaySummary ? `<div class="news-summary">${displaySummary}</div>` : ''}
        <button class="read-more-btn">Read More</button>
    `;

    // Add click handler to open modal
    const readMoreBtn = card.querySelector('.read-more-btn');
    readMoreBtn.addEventListener('click', () => {
        openArticleModal(item);
    });

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

        statsDiv.textContent = statsText;
    }
}

// Update pagination controls visibility
function updatePaginationControls() {
    const paginationControls = document.getElementById('paginationControls');
    const loadMoreBtn = document.getElementById('loadMoreBtn');

    if (hasMore && !isLoading) {
        paginationControls.style.display = 'flex';
        loadMoreBtn.textContent = 'Load More';
        loadMoreBtn.disabled = false;
    } else if (isLoading) {
        loadMoreBtn.textContent = 'Loading...';
        loadMoreBtn.disabled = true;
    } else {
        paginationControls.style.display = 'none';
    }
}

