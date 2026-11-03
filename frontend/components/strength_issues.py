from typing import Any, Dict, List
import streamlit as st


def display_strengths(strengths: List[str]) -> None:
    st.markdown("### 💪 Strengths")
    if not strengths:
        st.info("Keep improving your resume to unlock strengths!")
        return
    for item in strengths:
        st.markdown(f"- {item}")


def display_critical_issues(analysis: Dict[str, Any]) -> None:
    critical = list(analysis.get("critical_issues") or [])
    summary = analysis.get("issues_summary") or []
    detailed_feedback = analysis.get("detailed_feedback") or []

    # The API may leave critical_issues empty while still returning severity
    # on detailed_feedback. Derive urgent titles from those severity values.
    for issue in detailed_feedback:
        severity = (issue.get("severity_level") or "").strip().lower()
        title = issue.get("issue_title")
        if severity in {"critical", "high"} and title and title not in critical:
            critical.append(title)

    if not critical:
        lower_priority = [item for item in summary if item not in critical]
        if not lower_priority:
            st.markdown("### ✅ Critical Issues")
            st.success("No critical issues found. Your resume has no urgent findings.")
            return

        st.markdown("### ⚠️ Other Findings")
        st.info(
            f"No critical issues were flagged. {len(lower_priority)} lower-severity "
            "finding(s) are listed for review."
        )
        with st.expander("📋 View flagged items", expanded=False):
            for item in lower_priority:
                st.markdown(f"- {item}")
        return

    st.markdown("### 🚨 Critical Issues")
    st.error("These high-priority issues should be addressed first.")

    for item in critical:
        st.markdown(f"- {item}")

    extra = [item for item in summary if item not in critical]
    if extra:
        with st.expander("📋 Additional flagged items", expanded=False):
            for item in extra:
                st.markdown(f"- {item}")
