from datetime import datetime
from typing import List

import numpy as np

from prazo.core.logger import logger
from prazo.schemas import NewsItem
from prazo.utils.chat_models import ChatModel, EmbeddingModel


def get_embeddings(combined_articles: List[str]) -> List[List[float]]:
    embedding_model = EmbeddingModel(
        provider="openai", model_name="text-embedding-3-small"
    ).get_model()
    embeddings = embedding_model.embed_documents(combined_articles)
    return embeddings


def cosine_similarity(
    embedding1: List[float], embedding2: List[float]
) -> float:
    """
    Calculate cosine similarity between two embeddings.

    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector

    Returns:
        float: Cosine similarity score between 0 and 1
    """
    arr1 = np.array(embedding1)
    arr2 = np.array(embedding2)

    # Calculate cosine similarity
    dot_product = np.dot(arr1, arr2)
    norm1 = np.linalg.norm(arr1)
    norm2 = np.linalg.norm(arr2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    similarity = dot_product / (norm1 * norm2)

    # Convert from [-1, 1] to [0, 1] range
    return (similarity + 1) / 2


def merge_two_articles(article1: NewsItem, article2: NewsItem) -> NewsItem:
    """
    Merge two similar news items using the SMALL model for intelligent merging.
    Merge only title and summary. Rest can be derived from both articles.

    Args:
        article1: First news item
        article2: Second news item

    Returns:
        NewsItem: Merged news item
    """
    # Get the small model for merging
    llm = ChatModel(provider="openai", model_name="gpt-4o-mini").llm()

    # Create merge prompt
    merge_prompt = f"""You are tasked with merging two similar news items into one comprehensive item.

    **News Item 1:**
    Title: {article1.title}
    Summary: {article1.summary}

    **News Item 2:**
    Title: {article2.title}
    Summary: {article2.summary}

    Please merge the title and summary:
    1. For the title: Choose the most descriptive and accurate title from the two, OR if they cover significantly different aspects, create a merged title that captures both. Preserve the exact wording when possible.
    2. For the summary: Combine information from both summaries into a comprehensive summary (150-250 words) that covers all key points from both items.

    Return your response in this exact format:
    TITLE: [selected or merged title]
    SUMMARY: [merged summary]"""

    try:
        response = llm.invoke(merge_prompt)
        content = response.content.strip()

        # Parse the response
        lines = content.split("\n")
        merged_title = ""
        merged_summary = ""

        current_section = ""
        for line in lines:
            line = line.strip()
            if line.startswith("TITLE:"):
                merged_title = line.replace("TITLE:", "").strip()
                current_section = "title"
            elif line.startswith("SUMMARY:"):
                merged_summary = line.replace("SUMMARY:", "").strip()
                current_section = "summary"
            elif line and current_section == "summary":
                # Continue building summary if it spans multiple lines
                merged_summary += " " + line

        # Combine sources from both items and remove duplicates
        all_sources = list(set(article1.sources + article2.sources))
        
        # Combine topics and tool_sources from both items and remove duplicates
        all_topics = list(set(article1.topic + article2.topic))
        all_tool_sources = list(set(article1.tool_source + article2.tool_source))

        # Combine groups (they should be similar for duplicates)
        all_groups = list(set(article1.groups + article2.groups))
        
        # Use the earlier created_at timestamp (when content was originally created)
        earliest_created_at = min(article1.created_at, article2.created_at)

        return NewsItem(
            title=merged_title or article1.title,  # Fallback to first article's title
            summary=merged_summary
            or f"{article1.summary}\n\n{article2.summary}",  # Fallback
            sources=all_sources,
            published_date=(
                max(
                    d
                    for d in [article1.published_date, article2.published_date]
                    if d is not None
                )
                if any([article1.published_date, article2.published_date])
                else None
            ),
            topic=all_topics,
            groups=all_groups,
            tool_source=all_tool_sources,
            created_at=earliest_created_at,
            updated_at=datetime.now(),  # Set to now since we're merging/updating
        )
    except Exception as e:
        logger.warning(
            f"Error merging news items with LLM: {e}. Using simple merge."
        )
        # Fallback: simple merge
        # Use the earlier created_at timestamp
        earliest_created_at = min(article1.created_at, article2.created_at)
        
        return NewsItem(
            title=article1.title,  # Use first article's title as fallback
            summary=f"{article1.summary}\n\n{article2.summary}",
            sources=list(set(article1.sources + article2.sources)),
            published_date=article1.published_date or article2.published_date,
            topic=list(set(article1.topic + article2.topic)),
            groups=list(set(article1.groups + article2.groups)),
            tool_source=list(set(article1.tool_source + article2.tool_source)),
            created_at=earliest_created_at,
            updated_at=datetime.now(),  # Set to now since we're merging/updating
        )


def merge_similar_articles(
    articles: List[NewsItem], similar_articles: List[List[int]]
) -> List[NewsItem]:
    """
    Make list of similar articles.
    Pass two items at once to LLM to summarize the similar articles.
    Repeat until all similar articles are processed.
    Extract response into NewsItem.
    Return list of NewsItem.
    """
    deduplicated_articles = []
    for similar_article_indices in similar_articles:
        merged_article = articles[similar_article_indices[0]]
        if len(similar_article_indices) > 1:
            logger.info(
                f"Merging {len(similar_article_indices)} similar articles: {similar_article_indices}"
            )
            for article2_index in similar_article_indices[1:]:
                article2 = articles[article2_index]
                merged_article = merge_two_articles(merged_article, article2)
        deduplicated_articles.append(merged_article)
    return deduplicated_articles


def combine_article(article: NewsItem):
    """Combine title and summary"""
    return f"{article.title}\n{article.summary}"


def compare_embeddings(embeddings: List[List[float]]) -> List[List[float]]:
    """Compare embeddings to find similar articles"""
    # Track similar articles with their indices
    # i -> (j1, j2, j3, ...) => article i is similar to articles j1, j2, j3, ...
    # Return a list of indices [i, j1, j2, j3, ...] for each article. It implies article indices i, j1, j2, j3, ... are similar to each other.
    similar_articles = []
    merged_indices = []
    for i in range(len(embeddings)):
        if i in merged_indices:
            continue
        current_similar_articles = [i]
        for j in range(i + 1, len(embeddings)):
            similarity = cosine_similarity(embeddings[i], embeddings[j])
            if similarity >= 0.90:
                current_similar_articles.append(j)
                merged_indices.append(j)
        similar_articles.append(current_similar_articles)

    logger.info(
        f"Found {len(similar_articles)} unique article groups (threshold: 0.90)"
    )
    return similar_articles


def deduplicate(articles: List[NewsItem]) -> List[NewsItem]:
    logger.info(f"Starting deduplication for {len(articles)} articles")

    # If no articles, return empty list
    if len(articles) == 0 or len(articles) == 1:
        logger.info(f"No articles to deduplicate")
        return articles

    # Combine articles
    combined_articles: List[str] = [
        combine_article(article) for article in articles
    ]

    # Generate embeddings
    embeddings: List[List[float]] = get_embeddings(combined_articles)

    # Compare embeddings to find similar articles
    similar_articles: List[List[int]] = compare_embeddings(embeddings)

    # Merge similar articles
    deduplicated_articles = merge_similar_articles(articles, similar_articles)

    # Return merged articles in form of NewsItem
    logger.info(
        f"Deduplication complete: {len(articles)} → {len(deduplicated_articles)} articles"
    )
    return deduplicated_articles
