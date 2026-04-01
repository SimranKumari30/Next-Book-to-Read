"""
recommender.py
Finds semantically similar books using Claude for reasoning + Google Books for metadata.
Uses embedding_text from signals for rich semantic matching rather than keyword search.
"""

import json
import requests
import anthropic

client = anthropic.Anthropic()
GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"


RECOMMENDATION_PROMPT = """You are an expert literary curator who finds books that readers will love based on deep narrative and thematic similarity.

A reader loved: "{source_title}"

Here are the extracted plot signals from that book:
- Themes: {themes}
- Setting: {setting}
- Narrative Style: {narrative_style}
- Emotional Tone: {emotional_tone}
- Story Tropes: {tropes}
- Pacing: {pacing}
- Reader Profile: {audience_feel}
- Essence: {embedding_text}

Find {num_recs} books that share the deepest narrative and emotional DNA with this book.
Do NOT recommend the same book or books by the same author.
Do NOT just match genre — find books that feel similar to read, regardless of genre.

Return a JSON array of objects, each with:
{{
  "title": "exact book title",
  "author": "author full name",
  "why_it_matches": "2 sentences explaining the specific narrative/thematic connections to {source_title}",
  "shared_signals": ["3-4 specific signals this book shares with {source_title}"],
  "similarity_score": 0.0-1.0 float representing how similar this is
}}

Order by similarity score descending.
Return ONLY valid JSON array, no preamble."""


def find_similar_books(signals: dict, source_title: str, num_recs: int = 5) -> list[dict]:
    """
    Uses Claude to find similar books, then enriches with Google Books metadata.
    """
    if not signals:
        return []

    prompt = RECOMMENDATION_PROMPT.format(
        source_title=source_title,
        themes=", ".join(signals.get("themes", [])),
        setting=", ".join(signals.get("setting", [])),
        narrative_style=", ".join(signals.get("narrative_style", [])),
        emotional_tone=", ".join(signals.get("emotional_tone", [])),
        tropes=", ".join(signals.get("tropes", [])),
        pacing=signals.get("pacing", ""),
        audience_feel=signals.get("audience_feel", ""),
        embedding_text=signals.get("embedding_text", ""),
        num_recs=num_recs
    )

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        recommendations = json.loads(raw)

    except Exception as e:
        print(f"Recommendation generation failed: {e}")
        return []

    # Enrich each recommendation with Google Books metadata
    enriched = []
    for rec in recommendations:
        enriched_rec = _enrich_with_google_books(rec)
        enriched.append(enriched_rec)

    return enriched


def _enrich_with_google_books(rec: dict) -> dict:
    """
    Fetches cover image and rating data from Google Books for a recommendation.
    """
    try:
        query = f"{rec['title']} {rec.get('author', '')}"
        params = {"q": query, "maxResults": 1, "printType": "books"}
        resp = requests.get(GOOGLE_BOOKS_URL, params=params, timeout=8)
        resp.raise_for_status()
        items = resp.json().get("items", [])

        if items:
            volume = items[0]["volumeInfo"]
            image_links = volume.get("imageLinks", {})
            cover_url = (
                image_links.get("thumbnail", "")
                .replace("zoom=1", "zoom=2")
                .replace("http://", "https://")
            )
            # Google Books doesn't expose Goodreads ratings directly,
            # but averageRating is available for some books
            rating = volume.get("averageRating")

            rec["cover_url"] = cover_url
            if rating:
                rec["rating"] = rating

    except Exception as e:
        print(f"Google Books enrichment failed for {rec.get('title')}: {e}")

    return rec
