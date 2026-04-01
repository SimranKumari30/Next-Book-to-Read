"""
llm_analyzer.py
Uses Claude to extract structured plot signals from book description/excerpt.
Goes beyond keywords — extracts themes, emotional tone, narrative style, tropes.
"""

import json
import anthropic

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env


EXTRACTION_PROMPT = """You are a literary analyst specializing in identifying what makes books emotionally and narratively compelling.

Given the following book information, extract structured plot signals that capture the *essence* of the reading experience — not just genre labels.

Book Title: {title}
Author: {author}
Description/Excerpt:
{text}

Return a JSON object with these exact keys:
{{
  "themes": [4-6 core thematic elements, e.g. "identity and belonging", "power corrupts", "found family"],
  "setting": [3-4 descriptors, e.g. "epic world-building", "1930s Japan", "post-apocalyptic"],
  "narrative_style": [3-4 descriptors, e.g. "slow burn", "multiple POVs", "unreliable narrator", "lyrical prose"],
  "emotional_tone": [3-5 descriptors, e.g. "bittersweet", "hopeful", "tense", "melancholic"],
  "tropes": [3-5 story tropes, e.g. "chosen one", "enemies to lovers", "found family", "hero's journey"],
  "pacing": "one of: slow and immersive / medium / fast-paced and propulsive",
  "audience_feel": "1-2 sentence description of the kind of reader who would love this book",
  "embedding_text": "A rich 3-4 sentence description optimized for semantic similarity search — capture the plot feel, themes, tone, and narrative style in natural language"
}}

Be specific and evocative. Avoid generic labels like "good vs evil" — go deeper.
Return ONLY valid JSON, no preamble or explanation."""


def extract_plot_signals(book_data: dict) -> dict | None:
    """
    Sends book data to Claude and extracts structured plot signals.
    Returns parsed dict or None on failure.
    """
    text = book_data.get("excerpt") or book_data.get("description", "")
    if not text:
        return None

    # Truncate to avoid token limits — 2000 chars is plenty for signal extraction
    text = text[:2000]

    prompt = EXTRACTION_PROMPT.format(
        title=book_data.get("title", "Unknown"),
        author=book_data.get("author", "Unknown"),
        text=text
    )

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = response.content[0].text.strip()

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        signals = json.loads(raw)
        return signals

    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"LLM extraction failed: {e}")
        return None
