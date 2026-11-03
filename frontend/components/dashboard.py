from typing import Any, Dict

import streamlit as st

from frontend.components.score_display import display_overall_score, display_score_breakdown
from frontend.components.strength_issues import display_strengths, display_critical_issues
from frontend.components.skill_validation import display_skill_validation
from frontend.components.jd_comparison import display_jd_comparison
from frontend.components.detailed_feedback import display_detailed_feedback
from frontend.components.action_items import display_action_items
from frontend.components.recommendations import display_recommendations


def _open_job_search() -> None:
    """Switch the scorer to its optional job discovery mode."""
    st.session_state["analysis_mode"] = "Find Matching Remote Jobs"


def display_results_dashboard(analysis: Dict[str, Any]) -> None:
    """
    Render the full results page from one backend response dict.

    `analysis` is the JSON body returned by POST /api/v1/analyze-resume
    (i.e. an AnalysisResponse). No transformation is done here — every
    section reads the fields it needs directly.
    """
    display_overall_score(analysis)
    jd_comparison = analysis.get("jd_comparison") or analysis.get("jd_match_analysis")
    if jd_comparison:
        display_jd_comparison(jd_comparison)
        st.markdown("---")

    st.markdown("---")
    st.markdown("#### Next step")
    with st.container(border=True):
        prompt_col, button_col = st.columns([3, 1])
        with prompt_col:
            st.markdown("#### 🔎 Find your next opportunity")
            st.write(
                "Search by role and location. Compare a listing in Job Description Comparison."
            )
        with button_col:
            st.button(
                "Explore opportunities",
                key="open_job_search_from_results",
                on_click=_open_job_search,
                type="primary",
                use_container_width=True,
            )
    st.markdown("---")

    display_score_breakdown(analysis)
    st.markdown("---")

    display_strengths(analysis.get("strengths") or [])
    st.markdown("---")

    display_critical_issues(analysis)
    st.markdown("---")

    display_skill_validation(analysis)
    st.markdown("---")

    # Detailed resume feedback is generated for resume-only analyses too; it
    # should not depend on whether a job description was submitted.
    display_detailed_feedback(analysis)
    st.markdown("---")

    display_action_items(analysis)
    st.markdown("---")

    if jd_comparison:
        display_recommendations(analysis)
