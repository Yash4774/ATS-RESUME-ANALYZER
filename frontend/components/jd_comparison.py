from typing import Any, Dict, Optional

import streamlit as st


def display_jd_comparison(jd_comparison: Optional[Dict[str, Any]]) -> None:
    if not jd_comparison:
        return  # caller decides whether to render the section at all

    st.markdown("### 🎯 Resume-to-Opportunity Match")

    match_pct = float(jd_comparison.get("match_percentage", 0))
    semantic = float(jd_comparison.get("semantic_similarity", 0))
    match_progress = min(max(match_pct / 100.0, 0.0), 1.0)
    semantic_progress = min(max(semantic, 0.0), 1.0)
    matched = jd_comparison.get("matched_keywords", []) or []
    missing = jd_comparison.get("missing_keywords", []) or []
    gap = jd_comparison.get("skills_gap", []) or []

    with st.container(border=True):
        score_col, semantic_col = st.columns([2, 1])
        with score_col:
            st.metric("Match to this opportunity", f"{match_pct:.0f}%")
            st.progress(match_progress)
            st.caption("Based on the resume and the job description you provided.")
        with semantic_col:
            st.metric("Semantic similarity", f"{semantic * 100:.0f}%")
            st.progress(semantic_progress)

    st.markdown("---")
    st.markdown("#### Match details")
    matched_col, missing_col, gap_col = st.columns(3)
    sections = [
        (matched_col, "✅ Matched keywords", matched, "No matched keywords returned."),
        (missing_col, "🔎 Missing keywords", missing, "No missing keywords returned."),
        (gap_col, "🧩 Skills to strengthen", gap, "No skills gap returned."),
    ]
    for column, heading, items, empty_message in sections:
        with column, st.container(border=True):
            st.markdown(f"**{heading}**")
            if items:
                st.write(", ".join(str(item) for item in items[:12]))
                if len(items) > 12:
                    with st.expander(f"Show all {len(items)} items"):
                        st.write(", ".join(str(item) for item in items[12:]))
            else:
                st.caption(empty_message)
