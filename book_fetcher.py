"""
book_fetcher.py
Fetches book metadata, description, and excerpt from Google Books + Open Library.
"""

import requests


GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"
OPEN_LIBRARY_SEARCH = "https://openlibrary.org/search.json"
OPEN_LIBRARY_WORKS = "https://openlibrary.org"


def get_book_data(title: str) -> dict | None:
    """
    Main entry point. Tries Google Books first, falls back to Open Library.
    Returns a unified dict with: title, author, description, excerpt, cover_url, year.
    """
    data = _fetch_google_books(title)
    if not data:
        data = _fetch_open_library(title)
    return data


def _fetch_google_books(title: str) -> dict | None:
    """Fetch from Google Books API (no key needed for basic queries)."""
    try:
        params = {"q": title, "maxResults": 1, "printType": "books"}
        resp = requests.get(GOOGLE_BOOKS_URL, params=params, timeout=10)
        resp.raise_for_status()
        items = resp.json().get("items", [])
        if not items:
            return None

        volume = items[0]["volumeInfo"]
        authors = volume.get("authors", ["Unknown"])
        description = volume.get("description", "")

        # Try to get a longer excerpt via Open Library as supplement
        ol_data = _fetch_open_library(title)
        excerpt = ol_data.get("excerpt", "") if ol_data else ""

        # Cover image
        image_links = volume.get("imageLinks", {})
        cover_url = (
            image_links.get("thumbnail", "")
            .replace("zoom=1", "zoom=2")  # higher res
            .replace("http://", "https://")
        )

        return {
            "title": volume.get("title", title),
            "author": ", ".join(authors),
            "description": description,
            "excerpt": excerpt or description,  # fall back to description if no excerpt
            "cover_url": cover_url,
            "year": volume.get("publishedDate", "")[:4],
            "categories": volume.get("categories", []),
            "page_count": volume.get("pageCount", 0),
        }

    except Exception as e:
        print(f"Google Books fetch failed: {e}")
        return None


def _fetch_open_library(title: str) -> dict | None:
    """Fetch from Open Library — good for excerpts and edition data."""
    try:
        params = {"title": title, "limit": 1, "fields": "key,title,author_name,first_sentence,cover_i,first_publish_year"}
        resp = requests.get(OPEN_LIBRARY_SEARCH, params=params, timeout=10)
        resp.raise_for_status()
        docs = resp.json().get("docs", [])
        if not docs:
            return None

        doc = docs[0]
        work_key = doc.get("key", "")

        # Try to get the full work description
        description = ""
        excerpt = ""
        if work_key:
            work_resp = requests.get(f"{OPEN_LIBRARY_WORKS}{work_key}.json", timeout=10)
            if work_resp.ok:
                work_data = work_resp.json()
                desc = work_data.get("description", "")
                if isinstance(desc, dict):
                    description = desc.get("value", "")
                elif isinstance(desc, str):
                    description = desc

                # First sentence as excerpt proxy
                first_sentence = doc.get("first_sentence", [])
                if isinstance(first_sentence, list) and first_sentence:
                    excerpt = first_sentence[0]
                elif isinstance(first_sentence, str):
                    excerpt = first_sentence

        # Cover from Open Library
        cover_id = doc.get("cover_i")
        cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else ""

        return {
            "title": doc.get("title", title),
            "author": ", ".join(doc.get("author_name", ["Unknown"])),
            "description": description,
            "excerpt": excerpt or description[:500],
            "cover_url": cover_url,
            "year": str(doc.get("first_publish_year", "")),
            "categories": [],
            "page_count": 0,
        }

    except Exception as e:
        print(f"Open Library fetch failed: {e}")
        return None
