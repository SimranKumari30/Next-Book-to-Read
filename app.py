import streamlit as st
from book_fetcher import get_book_data
from llm_analyzer import extract_plot_signals
from recommender import find_similar_books
from review_fetcher import get_reviews

st.set_page_config(
    page_title="PlotMatch",
    page_icon="📚",
    layout="wide"
)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Inter:wght@300;400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0f0f0f;
        color: #e8e0d5;
    }
    .main { background-color: #0f0f0f; }
    .stTextInput > div > div > input {
        background-color: #1a1a1a;
        color: #e8e0d5;
        border: 1px solid #333;
        border-radius: 8px;
        font-size: 16px;
        padding: 12px;
    }
    .stButton > button {
        background-color: #c8a96e;
        color: #0f0f0f;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        font-size: 15px;
        padding: 10px 28px;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background-color: #e0c285;
        transform: translateY(-1px);
    }
    .book-card {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        transition: border-color 0.2s;
    }
    .book-card:hover { border-color: #c8a96e; }
    .book-title {
        font-family: 'Playfair Display', serif;
        font-size: 20px;
        font-weight: 700;
        color: #e8e0d5;
        margin-bottom: 4px;
    }
    .book-author { color: #c8a96e; font-size: 14px; margin-bottom: 12px; }
    .signal-tag {
        display: inline-block;
        background: #2a2a2a;
        color: #c8a96e;
        border: 1px solid #c8a96e33;
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 12px;
        margin: 3px;
    }
    .similarity-bar {
        background: #2a2a2a;
        border-radius: 4px;
        height: 6px;
        margin: 8px 0;
    }
    .similarity-fill {
        background: linear-gradient(90deg, #c8a96e, #e0c285);
        border-radius: 4px;
        height: 6px;
    }
    .review-quote {
        background: #111;
        border-left: 3px solid #c8a96e;
        border-radius: 0 8px 8px 0;
        padding: 12px 16px;
        font-size: 13px;
        color: #aaa;
        font-style: italic;
        margin: 8px 0;
    }
    .rating-badge {
        background: #2a2a2a;
        color: #c8a96e;
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 13px;
        font-weight: 600;
    }
    .source-input-card {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
    }
    h1 { font-family: 'Playfair Display', serif !important; }
    .subtitle { color: #888; font-size: 16px; margin-bottom: 32px; }
    .signal-section { margin: 16px 0; }
    .signal-label { font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
</style>
""", unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 📚 PlotMatch")
st.markdown('<p class="subtitle">Find your next book based on what you loved about the last one — powered by semantic plot analysis, not just genre tags.</p>', unsafe_allow_html=True)

# ── Input ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="source-input-card">', unsafe_allow_html=True)
col1, col2 = st.columns([3, 1])
with col1:
    book_title = st.text_input(
        "Enter a book you loved",
        placeholder="e.g. The Name of the Wind, Pachinko, Dune...",
        label_visibility="collapsed"
    )
with col2:
    num_recs = st.selectbox("Recommendations", [3, 5, 8], index=1, label_visibility="collapsed")
search_clicked = st.button("Find Similar Books →")
st.markdown('</div>', unsafe_allow_html=True)

# ── Main Logic ────────────────────────────────────────────────────────────────
if search_clicked and book_title:
    # Step 1: Fetch book data
    with st.spinner(f'Finding "{book_title}"...'):
        book_data = get_book_data(book_title)

    if not book_data:
        st.error("Couldn't find that book. Try a slightly different title or check spelling.")
        st.stop()

    # Show source book
    st.markdown("---")
    st.markdown("**Analyzing:**")
    src_col1, src_col2 = st.columns([1, 4])
    with src_col1:
        if book_data.get("cover_url"):
            st.image(book_data["cover_url"], width=100)
    with src_col2:
        st.markdown(f'<div class="book-title">{book_data["title"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="book-author">by {book_data.get("author", "Unknown")}</div>', unsafe_allow_html=True)
        if book_data.get("description"):
            st.markdown(f'<small style="color:#666">{book_data["description"][:300]}...</small>', unsafe_allow_html=True)

    # Step 2: LLM extraction
    with st.spinner("Extracting plot signals, themes, and narrative style..."):
        signals = extract_plot_signals(book_data)

    if signals:
        st.markdown("---")
        st.markdown("**What PlotMatch found in this book:**")
        cols = st.columns(3)
        signal_groups = [
            ("🎭 Themes", signals.get("themes", [])),
            ("🌍 Setting & World", signals.get("setting", [])),
            ("💬 Narrative Style", signals.get("narrative_style", [])),
        ]
        for i, (label, items) in enumerate(signal_groups):
            with cols[i]:
                st.markdown(f'<div class="signal-label">{label}</div>', unsafe_allow_html=True)
                tags = " ".join([f'<span class="signal-tag">{item}</span>' for item in items])
                st.markdown(tags, unsafe_allow_html=True)

        tone_items = signals.get("emotional_tone", [])
        trope_items = signals.get("tropes", [])
        if tone_items or trope_items:
            st.markdown("")
            cols2 = st.columns(2)
            with cols2[0]:
                st.markdown('<div class="signal-label">❤️ Emotional Tone</div>', unsafe_allow_html=True)
                tags = " ".join([f'<span class="signal-tag">{item}</span>' for item in tone_items])
                st.markdown(tags, unsafe_allow_html=True)
            with cols2[1]:
                st.markdown('<div class="signal-label">✨ Story Tropes</div>', unsafe_allow_html=True)
                tags = " ".join([f'<span class="signal-tag">{item}</span>' for item in trope_items])
                st.markdown(tags, unsafe_allow_html=True)

    # Step 3: Find similar books
    st.markdown("---")
    st.markdown(f"### Books you'll likely love")
    st.markdown('<p style="color:#666; font-size:13px;">Matched by plot signals, themes, and narrative style — not just genre.</p>', unsafe_allow_html=True)

    with st.spinner(f"Finding {num_recs} semantically similar books..."):
        recommendations = find_similar_books(signals, book_data["title"], num_recs)

    if not recommendations:
        st.warning("Couldn't generate recommendations. Check your API key and try again.")
        st.stop()

    # Step 4: Show recommendations with reviews
    for i, rec in enumerate(recommendations):
        st.markdown('<div class="book-card">', unsafe_allow_html=True)

        rec_col1, rec_col2 = st.columns([1, 5])
        with rec_col1:
            if rec.get("cover_url"):
                st.image(rec["cover_url"], width=90)
            else:
                st.markdown('<div style="width:90px;height:130px;background:#2a2a2a;border-radius:6px;display:flex;align-items:center;justify-content:center;color:#555;font-size:24px">📖</div>', unsafe_allow_html=True)

        with rec_col2:
            st.markdown(f'<div class="book-title">{rec["title"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="book-author">by {rec.get("author", "Unknown")}</div>', unsafe_allow_html=True)

            # Similarity score bar
            score = rec.get("similarity_score", 0.7)
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;margin:8px 0">'
                f'<div class="similarity-bar" style="flex:1"><div class="similarity-fill" style="width:{int(score*100)}%"></div></div>'
                f'<span style="color:#c8a96e;font-size:13px;font-weight:600">{int(score*100)}% match</span>'
                f'</div>',
                unsafe_allow_html=True
            )

            # Why it matches
            if rec.get("why_it_matches"):
                st.markdown(f'<p style="color:#aaa;font-size:14px;margin:8px 0">{rec["why_it_matches"]}</p>', unsafe_allow_html=True)

            # Shared signals
            shared = rec.get("shared_signals", [])
            if shared:
                tags = " ".join([f'<span class="signal-tag">{s}</span>' for s in shared])
                st.markdown(tags, unsafe_allow_html=True)

            # Rating
            if rec.get("rating"):
                st.markdown(f'<span class="rating-badge">⭐ {rec["rating"]} / 5 on Goodreads</span>', unsafe_allow_html=True)

        # Reviews
        with st.spinner(f'Fetching reader reviews for {rec["title"]}...'):
            reviews = get_reviews(rec["title"], rec.get("author", ""))

        if reviews:
            st.markdown("")
            for review in reviews[:2]:
                st.markdown(f'<div class="review-quote">"{review["text"]}" <span style="color:#555;font-style:normal">— {review["source"]}</span></div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

elif search_clicked and not book_title:
    st.warning("Please enter a book title first.")
