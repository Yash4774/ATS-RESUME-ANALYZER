from typing import Any, Dict, List

import streamlit as st

SEVERITY_ORDER = ["critical", "high", "medium", "low"]
SEVERITY_ALIASES = {"moderate": "medium", "info": "low"}


def _group_by_severity(issues: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {level: [] for level in SEVERITY_ORDER}
    for issue in issues:
        level = (issue.get("severity_level") or "low").strip().lower()
        level = SEVERITY_ALIASES.get(level, level)
        # Keep unexpected backend severity values visible instead of silently
        # dropping them when rendering only the known severity buckets below.
        if level not in grouped:
            level = "low"
        grouped[level].append(issue)
    return grouped


def _render_issue(issue: Dict[str, Any]) -> None:
    raw_level = (issue.get("severity_level") or "low").strip().lower()
    level = SEVERITY_ALIASES.get(raw_level, raw_level)
    if level not in SEVERITY_ORDER:
        level = "low"

    icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}[level]
    title = issue.get("issue_title") or "Untitled issue"
    impact = issue.get("ats_impact")
    explanation = issue.get("explanation")
    where = issue.get("where_it_appears")
    how_to_fix = issue.get("how_to_fix")
    action_items = issue.get("action_items") or []
    example = issue.get("example_improvement")

    with st.container(border=True):
        st.subheader(f"{icon} {title}")
        st.caption(f"{level.title()} priority")
        if explanation:
            st.markdown("**What's happening**")
            st.write(explanation)
        if impact:
            st.markdown("**ATS impact**")
            st.write(impact)
        if where:
            st.markdown("**Where it appears**")
            st.write(where)
        if how_to_fix:
            st.markdown("**How to fix**")
            st.write(how_to_fix)
        if action_items:
            st.markdown("**Action items:**")
            for item in action_items:
                st.markdown(f"- {item}")
        if example:
            st.markdown("**Example improvement:**")
            st.code(example, language="text")


def display_detailed_feedback(analysis: Dict[str, Any]) -> None:
    issues = analysis.get("detailed_feedback") or []
    if not issues:
        return  # backend produced no per-issue feedback this run

    st.markdown("### 🔍 Detailed Feedback")
    st.caption(f"{len(issues)} issue(s) flagged. Review the explanation and suggested fixes below.")

    grouped = _group_by_severity(issues)
    for level in SEVERITY_ORDER:
        items = grouped.get(level, [])
        if not items:
            continue
        st.markdown(f"#### {level.title()} ({len(items)})")
        for issue in items:
            _render_issue(issue)
