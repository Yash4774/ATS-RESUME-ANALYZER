from typing import Any, Dict

import streamlit as st


def display_recommendations(analysis: Dict[str, Any]) -> None:
    suggestions = analysis.get("suggestions") or []
    if not suggestions:
        # The current analyzer supplies per-issue fixes rather than a separate
        # suggestions list. Use those as the recommendation summary.
        suggestions = list(dict.fromkeys(
            issue.get("how_to_fix")
            for issue in analysis.get("detailed_feedback") or []
            if issue.get("how_to_fix")
        ))
    if not suggestions:
        return

    st.markdown("### 💡 Recommendations")
    for suggestion in suggestions:
        st.markdown(f"- {suggestion}")
