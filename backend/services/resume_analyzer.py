import spacy
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Optional
from backend.models.schemas import IssueDetail
from backend.services.groq_parser import parse_resume, parse_job_description
from backend.services.jd_matcher import compare_resume_with_jd
from backend.services.feedback_engine import analyze_issues, generate_issues_summary
from backend.services.ats_scorer import calculate_overall_score, validate_skills_with_projects


def analyze_full_resume(
    resume_text: str,
    nlp: spacy.Language,
    embedder: SentenceTransformer,
    job_description: Optional[str] = None,
) -> Dict:
    import logging
    logger = logging.getLogger('ats_resume_scorer')
    parsed_resume = parse_resume(resume_text)
    logger.info(f"Groq parsed summary: {parsed_resume.get('professional_summary', '')[:100]!r}")
    logger.info(f"Groq parsed skills count: {len(parsed_resume.get('skills', []))}")
    logger.info(f"Groq parsed experience count: {len(parsed_resume.get('experience', []))}")

    skills          = parsed_resume.get('skills', [])
    projects        = parsed_resume.get('projects', [])
    keywords        = parsed_resume.get('keywords', [])
    action_verbs    = parsed_resume.get('action_verbs', [])

    experience_months = sum(
        int(e.get('duration_months', 0))
        for e in parsed_resume.get('experience', [])
        if isinstance(e, dict)
    )

    contact_info = {
        'email':     parsed_resume.get('email'),
        'phone':     parsed_resume.get('phone'),
        'linkedin':  parsed_resume.get('linkedin'),
        'github':    parsed_resume.get('github'),
        'portfolio': None,
    }
    skill_validation = validate_skills_with_projects(
        skills=skills,
        projects=projects,
        experience_entries=parsed_resume.get('experience', []),
        embedder=embedder,
    )

    jd_comparison_result = None
    jd_keywords = None
    if job_description and job_description.strip():
        parsed_jd = parse_job_description(job_description.strip())
        jd_keywords = list(set(
            parsed_jd.get('keywords', []) +
            parsed_jd.get('required_skills', []) +
            parsed_jd.get('preferred_skills', [])
        ))
        jd_comparison_result = compare_resume_with_jd(
            resume_text=resume_text,
            resume_keywords=keywords,
            resume_skills=skills,
            jd_text=job_description.strip(),
            jd_keywords=jd_keywords,
            embedder=embedder,
            nlp=nlp,
        )

    from backend.utils.file_utils import (
        get_default_grammar_results, get_default_location_results,
    )
    grammar_results  = get_default_grammar_results()
    location_results = get_default_location_results()

    scores = calculate_overall_score(
        text=resume_text,
        parsed_resume=parsed_resume,
        skills=skills,
        keywords=keywords,
        action_verbs=action_verbs,
        skill_validation_results=skill_validation,
        grammar_results=grammar_results,
        location_results=location_results,
        jd_keywords=jd_keywords,
        experience_months=experience_months,
    )
    detailed_feedback = analyze_issues(
        resume_text=resume_text,
        parsed_resume=parsed_resume,
        skills=skills,
        projects=projects,
        action_verbs=action_verbs,
        skill_validation=skill_validation,
        scores=scores,
        contact_info=contact_info,
    )

    issues_summary = generate_issues_summary(detailed_feedback)

    validated_raw   = skill_validation.get('validated_skills', [])
    unvalidated_raw = skill_validation.get('unvalidated_skills', [])
    total_skills    = len(validated_raw) + len(unvalidated_raw)
    val_pct         = round((len(validated_raw) / total_skills * 100) if total_skills > 0 else 0, 1)

    skill_validation_details = {
        "validated": [
            {
                "skill":    item['skill'],
                "projects": item.get('projects', []),
            }
            for item in validated_raw
        ],
        "unvalidated":     unvalidated_raw,
        "total":           total_skills,
        "validated_count": len(validated_raw),
        "validation_pct":  val_pct,
    }

    return {
        "ATS_score":          scores['overall_score'],
        "ats_score":          scores['overall_score'],
        "component_scores": {
            "formatting":       scores['formatting_score'],
            "keywords":         scores['keywords_score'],
            "content":          scores['content_score'],
            "skill_validation": scores['skill_validation_score'],
            "ats_compatibility": scores['ats_compatibility_score'],
        },
        "issues_summary":    issues_summary,
        "detailed_feedback": detailed_feedback,
        "jd_match_analysis": jd_comparison_result,
        "jd_comparison":     jd_comparison_result,
        "skills":            skills,
        "matched_keywords":  (
            jd_comparison_result['matched_keywords']
            if jd_comparison_result else list(keywords[:20])
        ),
        "missing_keywords":  (
            jd_comparison_result['missing_keywords']
            if jd_comparison_result else []
        ),
        "strengths": _generate_strengths(parsed_resume, skills, projects, action_verbs, skill_validation, scores),
        "interpretation":    scores.get('overall_interpretation', ''),
        "skill_validation_details": skill_validation_details,
        "experience_months": experience_months,
    }


def _generate_strengths(
    parsed_resume: Dict, skills: List, projects: List,
    action_verbs: List, skill_validation: Dict, scores: Dict,
) -> List[str]:
    """Summarize positive resume evidence with concrete counts and score context."""
    strengths = []

    experience = parsed_resume.get('experience') or []
    education = parsed_resume.get('education') or []
    resume_projects = parsed_resume.get('projects') or []
    resume_skills = parsed_resume.get('skills') or []
    project_count = max(len(resume_projects), len(projects or []))

    if experience:
        count = len(experience) if isinstance(experience, (list, tuple)) else 1
        strengths.append(f"Experience section detected with {count} role or entry/entries.")
    if project_count:
        strengths.append(f"Projects section detected with {project_count} project(s) showing applied work.")
    if education:
        count = len(education) if isinstance(education, (list, tuple)) else 1
        strengths.append(f"Education section detected with {count} education entry/entries.")
    if resume_skills or skills:
        count = len(skills or resume_skills)
        strengths.append(f"Skills section detected with {count} skill(s) identified.")
    if (parsed_resume.get('professional_summary') or '').strip():
        strengths.append("A professional summary gives recruiters a quick overview of your background.")

    validated = skill_validation.get('validated_skills', [])
    unvalidated = skill_validation.get('unvalidated_skills', [])
    total = len(validated) + len(unvalidated)
    if validated:
        pct = len(validated) / total * 100 if total else 0
        strengths.append(f"{len(validated)} of {total} identified skills ({pct:.0f}%) are supported by project or experience evidence.")
    if action_verbs:
        strengths.append(f"Your experience uses {len(action_verbs)} action verb(s) to describe work performed.")

    formatting = scores.get('formatting_score', 0)
    content = scores.get('content_score', 0)
    if formatting >= 16:
        strengths.append(f"Strong ATS-friendly formatting: {formatting:.0f}/20 for structure and readability.")
    if content >= 20:
        strengths.append(f"Strong content quality: {content:.0f}/25 for achievements and supporting detail.")

    return strengths