"""
review_fetcher.py
Fetches real reader reviews from Reddit (r/books, r/Fantasy, r/suggestmeabook)
and Open Library community reviews.
No API keys needed — uses Reddit's public JSON endpoints.
"""

import requests
from urllib.parse import quote


REDDIT_SEARCH = "https://www.reddit.com/search.json"
REDDIT_HEADERS = {"User-Agent": "PlotMatch/1.0 (book recommendation app)"}

SUBREDDITS = ["books", "Fantasy", "suggestmeabook", "booksuggestions", "scifi"]


def get_reviews(title: str, author: str = "") -> list[dict]:
    """
    Fetches a mix of Reddit reader reviews/mentions for a book.
    Returns list of dicts with: text, source, score.
    """
    reviews = []

    reddit_reviews = _fetch_reddit_mentions(title, author)
    reviews.extend(reddit_reviews)

    # Deduplicate and return top reviews
    seen = set()
    unique = []
    for r in reviews:
        key = r["text"][:50]
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return unique[:3]  # top 3 reviews max


def _fetch_reddit_mentions(title: str, author: str) -> list[dict]:
    """
    Searches Reddit for posts/comments about the book.
    Extracts meaningful review snippets from top posts.
    """
    reviews = []

    try:
        # Search across book subreddits
        query = f'"{title}"'
        if author:
            query += f" {author.split()[-1]}"  # last name only

        params = {
            "q": query,
            "sort": "relevance",
            "limit": 10,
            "type": "link",
            "restrict_sr": False,
            "t": "year"  # past year
        }

        resp = requests.get(
            REDDIT_SEARCH,
            params=params,
            headers=REDDIT_HEADERS,
            timeout=10
        )

        if not resp.ok:
            return []

        posts = resp.json().get("data", {}).get("children", [])

        for post in posts:
            data = post.get("data", {})
            subreddit = data.get("subreddit", "")

            # Only pull from book-related subreddits
            if subreddit.lower() not in [s.lower() for s in SUBREDDITS]:
                continue

            selftext = data.get("selftext", "").strip()
            title_text = data.get("title", "").strip()
            score = data.get("score", 0)

            # Skip low-effort posts
            if score < 5:
                continue

            # Use selftext if it has substance, otherwise use title as snippet
            snippet = ""
            if selftext and len(selftext) > 80:
                # Extract a meaningful sentence or two
                sentences = [s.strip() for s in selftext.split(".") if len(s.strip()) > 40]
                # Filter out sentences that look like meta-commentary
                book_sentences = [
                    s for s in sentences
                    if any(word in s.lower() for word in [
                        "book", "read", "story", "character", "plot", "writing",
                        "author", "loved", "recommend", "favorite", "beautifully",
                        "amazing", "incredible", "prose", "narrative"
                    ])
                ]
                if book_sentences:
                    snippet = book_sentences[0][:200]
            elif len(title_text) > 40 and title_text != title:
                snippet = title_text[:200]

            if snippet:
                reviews.append({
                    "text": snippet,
                    "source": f"r/{subreddit}",
                    "score": score
                })

        # Sort by Reddit score
        reviews.sort(key=lambda x: x["score"], reverse=True)

    except Exception as e:
        print(f"Reddit fetch failed: {e}")

    return reviews[:3]
