from typing import Optional

import requests
import streamlit as st

from frontend.services import api_client
from frontend.services.job_search import (
    build_job_portals,
)
from frontend.components.dashboard import display_results_dashboard


def _read_jd(jd_file, jd_text: str) -> str:
    """
    Turn whatever the user provided into a plain JD string for the backend.

    For .txt files we decode in-process — that's a trivial operation, no need
    for a backend round-trip. For PDF/DOCX, we'd need the backend's parser;
    we don't have a public endpoint for that, so we ask the user to paste text
    instead for non-txt JDs.
    """
    if jd_text:
        return jd_text.strip()
    if jd_file is None:
        return ""
    if jd_file.name.lower().endswith(".txt"):
        return jd_file.getvalue().decode("utf-8", errors="ignore")
    st.warning(
        "Job description files must be `.txt` for now — paste the JD text instead "
        "if you have a PDF or DOCX."
    )
    return ""


def _show_backend_error(exc: Exception) -> None:
    """Translate a `requests` exception into a friendly Streamlit error."""
    if isinstance(exc, requests.ConnectionError):
        st.error("Could not reach the backend. Is `uvicorn backend.main:app` running on port 8000?")
    elif isinstance(exc, requests.Timeout):
        st.error("The backend took too long to respond. Try a smaller resume or check the server logs.")
    elif isinstance(exc, requests.HTTPError) and exc.response is not None:
        try:
            detail = exc.response.json().get("detail", exc.response.text)
        except ValueError:
            detail = exc.response.text
        st.error(f"Backend returned {exc.response.status_code}: {detail}")
    else:
        st.error(f"Unexpected error: {exc}")


def _summary_text(analysis: dict) -> str:
    """Tiny client-side text summary for the Download button."""
    score = analysis.get("ATS_score", analysis.get("ats_score", 0))
    lines = [f"ATS Score: {score:.0f}/100", ""]
    if analysis.get("strengths"):
        lines.append("STRENGTHS:")
        lines.extend(f"  - {s}" for s in analysis["strengths"])
        lines.append("")
    if analysis.get("critical_issues"):
        lines.append("CRITICAL ISSUES:")
        lines.extend(f"  - {s}" for s in analysis["critical_issues"])
        lines.append("")
    if analysis.get("suggestions"):
        lines.append("SUGGESTIONS:")
        lines.extend(f"  - {s}" for s in analysis["suggestions"])
    return "\n".join(lines)


def _render_upload_area(analysis_mode: str):
    """Two-column upload widgets. Returns (resume_file, jd_file, jd_text)."""
    left, right = st.columns(2)

    with left:
        st.markdown("### 📄 Upload Resume")
        resume_file = st.file_uploader(
            "Choose your resume file",
            type=["pdf", "doc", "docx"],
            help="Supported: PDF, DOC, DOCX (max 5 MB)",
            key="resume_upload",
        )
        if resume_file:
            st.success(f"✅ {resume_file.name} ({resume_file.size / 1024:.1f} KB)")

    jd_file: Optional[object] = None
    jd_text = ""

    with right:
        if analysis_mode == "Job Description Comparison":
            st.markdown("### 📋 Job Description")
            jd_method = st.radio(
                "Input method:",
                ["Paste Text", "Upload .txt File"],
                horizontal=True,
                key="jd_input_method",
            )
            if jd_method == "Upload .txt File":
                jd_file = st.file_uploader(
                    "Choose JD file (.txt only)",
                    type=["txt"],
                    key="jd_upload",
                )
                if jd_file:
                    st.success(f"✅ {jd_file.name}")
            else:
                jd_text = st.text_area(
                    "Paste job description text:",
                    height=200,
                    placeholder="Paste the JD here...",
                    key="jd_text",
                )
                if jd_text:
                    st.success(f"✅ {len(jd_text)} characters")
        else:
            st.markdown("### 📋 Job Description")
            st.info("Switch to 'Job Description Comparison' mode to enter a job description.")

    return resume_file, jd_file, jd_text


def _render_job_search() -> Optional[dict]:
    """Render searches on established job portals using the user's preferences."""
    if not st.session_state.get("access_token"):
        st.warning("🔒Please Sign In to Access Opportunity Search.")
        return None

    st.markdown("### 🔎 Opportunity Search")
    st.caption(
        "Choose your target role, location, opportunity type, and work preference. Open a portal search "
        "and apply directly on that site."
    )

    with st.form("remote_job_search_form"):
        role = st.text_input(
            "What role are you looking for?",
            placeholder="e.g. Python developer, data analyst, UX designer",
            key="remote_job_role",
        ).strip()
        location = st.text_input(
            "Where would you like to work?",
            placeholder="e.g. India, Bengaluru, United States (optional)",
            key="remote_job_location",
        ).strip()
        employment = st.selectbox(
            "Opportunity type",
            ["Any", "Internship", "Full-time", "Part-time", "Contract"],
            key="remote_job_type",
        )
        work_preference = st.selectbox(
            "Work preference",
            ["Any", "Remote", "Hybrid", "On-site"],
            key="remote_job_work_preference",
        )
        search_clicked = st.form_submit_button("Find matching portals", type="primary")

    if search_clicked:
        if not role:
            st.session_state.pop("job_portal_search", None)
            st.warning("Enter a role or a few skills to search for.")
        else:
            st.session_state["job_portal_search"] = {
                "role": role,
                "location": location,
                "opportunity_type": employment,
                "work_preference": work_preference,
                "portals": build_job_portals(role, location, employment, work_preference),
            }

    search = st.session_state.get("job_portal_search")
    if search:
        current = (role, location, employment, work_preference)
        submitted = (
            search["role"], search["location"], search["opportunity_type"], search["work_preference"]
        )
        if current == submitted:
            location_label = search["location"] or "any location"
            st.markdown(f"#### Portals for **{search['role']}** · {location_label}")
            st.caption(
                "Search terms are prefilled where the portal supports them. Internship-only portals "
                "appear when you select Internship. Review eligibility and application details on each site."
            )
            for start in range(0, len(search["portals"]), 2):
                portal_columns = st.columns(2)
                for column, portal in zip(portal_columns, search["portals"][start:start + 2]):
                    with column, st.container(border=True):
                        st.markdown(f"**{portal['name']}**")
                        st.caption(portal["description"])
                        st.link_button(portal["action"], portal["url"], use_container_width=True)
        else:
            st.info("Update your preferences and select **Find matching portals** to refresh these links.")
    return None


def _render_export_buttons(analysis: dict) -> None:
    st.markdown("### 📥 Export Results")
    c1, c2 = st.columns(2)

    with c1:
        # Lazy: only call the backend the first time the user clicks expand.
        if st.button("📑 Generate PDF Report", use_container_width=True, type="primary"):
            try:
                with st.spinner("Generating PDF on backend..."):
                    pdf_bytes = api_client.generate_pdf(
                        analysis,
                        access_token=st.session_state["access_token"],
                    )
                st.session_state["scorer_pdf_bytes"] = pdf_bytes
            except requests.RequestException as exc:
                _show_backend_error(exc)

        if "scorer_pdf_bytes" in st.session_state:
            st.download_button(
                "⬇️ Download PDF",
                data=st.session_state["scorer_pdf_bytes"],
                file_name="ats_resume_report.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="download_pdf_report",
            )

    with c2:
        st.download_button(
            "📄 Download Summary (.txt)",
            data=_summary_text(analysis),
            file_name="ats_summary.txt",
            mime="text/plain",
            use_container_width=True,
            key="download_summary",
        )


def render() -> None:
    st.title("🎯 ATS Resume Scorer")
    st.markdown("Upload your resume — and optionally a job description — for a comprehensive analysis.")

    with st.sidebar:
        st.markdown("---")
        st.markdown("## 📊 Analysis Options")
        st.info(
            "**General ATS Score**: resume only — overall compatibility.\n\n"
            "**JD Comparison**: resume + job description — targeted match analysis.\n\n"
            "**Opportunity Search**: find role- and location-focused listings and apply directly on the portal."
        )

    st.markdown("---")

    analysis_mode = st.radio(
        "Select Analysis Mode:",
        ["General ATS Score", "Job Description Comparison", "Find Matching Remote Jobs"],
        horizontal=True,
        format_func=lambda mode: "Opportunity Search" if mode == "Find Matching Remote Jobs" else mode,
        key="analysis_mode",
    )

    st.markdown("---")

    if analysis_mode == "Find Matching Remote Jobs":
        _render_job_search()
        return

    resume_file, jd_file, jd_text = _render_upload_area(analysis_mode)

    st.markdown("---")

    if not resume_file:
        previous_analysis = st.session_state.get("scorer_analysis")
        if previous_analysis:
            st.info("Showing your previous analysis. Upload a resume above to run a new one.")
            if analysis_mode != "Find Matching Remote Jobs":
                display_results_dashboard(previous_analysis)
        else:
            st.info("👆 Upload your resume to begin.")
        return

    access_token = st.session_state.get("access_token")
    if not access_token:
        st.warning("⚠️ Sign in from the sidebar to analyze a resume.")
        return

    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        analyze = st.button(
            "🚀 Analyze Resume",
            use_container_width=True,
            type="primary",
        )

    if not analyze:
        # Re-show previous result on rerun (e.g. after PDF generation).
        if analysis_mode != "Find Matching Remote Jobs" and st.session_state.get("scorer_analysis"):
            display_results_dashboard(st.session_state["scorer_analysis"])
            _render_export_buttons(st.session_state["scorer_analysis"])
        return

    # Fresh analysis — drop any cached PDF/result.
    st.session_state.pop("scorer_pdf_bytes", None)
    st.session_state.pop("scorer_analysis", None)

    if analysis_mode == "Job Description Comparison":
        job_description = _read_jd(jd_file, jd_text)
    else:
        job_description = ""

    try:
        with st.spinner("Analyzing your resume... this can take 10-30 seconds."):
            analysis = api_client.analyze_resume(
                resume_file=resume_file,
                access_token=access_token,
                job_description=job_description,
            )
    except requests.RequestException as exc:
        _show_backend_error(exc)
        return

    st.session_state["scorer_analysis"] = analysis
    st.success("✅ Analysis complete!")
    display_results_dashboard(analysis)
    _render_export_buttons(analysis)
