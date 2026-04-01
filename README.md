# 📚 PlotMatch

> Find your next book based on what you *loved* about the last one — powered by semantic plot analysis, not genre tags.

## What it does

Most book recommendation engines match on genre or author. PlotMatch goes deeper: it reads what makes a book *feel* the way it does — the emotional tone, narrative style, thematic DNA, pacing — and finds other books that share that essence, even across genres.

**Input:** A book title you loved  
**Output:** 5 recommended books with semantic similarity scores, shared plot signals, and real reader reviews from Reddit

## How it works

```
Book Title
    │
    ▼
┌─────────────────────┐
│   Book Fetcher      │  Google Books API + Open Library API
│   (book_fetcher.py) │  → title, author, description, excerpt, cover
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   LLM Analyzer      │  Claude (claude-sonnet-4)
│  (llm_analyzer.py)  │  → themes, setting, narrative style,
└──────────┬──────────┘    emotional tone, tropes, pacing
           │
           ▼
┌─────────────────────┐
│   Recommender       │  Claude semantic reasoning
│  (recommender.py)   │  → 5 books with similarity scores + reasoning
└──────────┬──────────┘    enriched with Google Books covers/ratings
           │
           ▼
┌─────────────────────┐
│   Review Fetcher    │  Reddit public API (no key needed)
│  (review_fetcher.py)│  → real reader quotes from r/books,
└──────────┬──────────┘    r/Fantasy, r/suggestmeabook
           │
           ▼
    Streamlit UI (app.py)
```

## Why not just keyword search?

Keyword search would match "The Name of the Wind" with other fantasy books tagged "magic system." PlotMatch instead understands that what readers loved was the *unreliable narrator*, the *coming-of-age in an academy setting*, the *lyrical first-person prose*, and the *bittersweet melancholy* — and finds books that share those signals, even if they're literary fiction or sci-fi.

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set your Anthropic API key
```bash
export ANTHROPIC_API_KEY=your_key_here
```
Get a key at [console.anthropic.com](https://console.anthropic.com)

### 3. Run
```bash
streamlit run app.py
```

## Example

Input: **"Pachinko"** by Min Jin Lee

PlotMatch extracts:
- Themes: *generational trauma, identity & belonging, sacrifice, survival*
- Narrative Style: *multi-generational saga, third-person omniscient, slow burn*
- Emotional Tone: *melancholic, hopeful, bittersweet*
- Tropes: *family saga, immigrant experience, historical backdrop*

Recommendations might include:
- *A Little Life* (Hanya Yanagihara) — shared emotional weight and generational trauma
- *The Kite Runner* (Khaled Hosseini) — shared immigrant experience and bittersweet tone
- *Homegoing* (Yaa Gyasi) — shared multi-generational saga structure

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | Anthropic Claude (claude-sonnet-4) |
| Book Metadata | Google Books API + Open Library API |
| Reader Reviews | Reddit public JSON API |
| UI | Streamlit |
| Language | Python 3.11+ |

## Project Structure

```
plotmatch/
├── app.py              # Streamlit UI — main entry point
├── book_fetcher.py     # Fetches book metadata from Google Books + Open Library
├── llm_analyzer.py     # LLM-based plot signal extraction
├── recommender.py      # Semantic recommendation engine + Google Books enrichment
├── review_fetcher.py   # Reddit review fetcher
├── requirements.txt
└── README.md
```

## API Usage & Cost

- **Google Books API**: Free, no key required for basic queries
- **Open Library API**: Free, no key required
- **Reddit API**: Free public JSON endpoint, no key required
- **Anthropic API**: ~$0.01-0.03 per search (2 Claude calls per query)

## Future Ideas

- Add vector embeddings (e.g. via `sentence-transformers`) for pure semantic search across a pre-built book corpus
- Integrate Goodreads data via scraping or unofficial API
- Add user reading history to personalize recommendations over time
- Export reading list to Goodreads or Notion
