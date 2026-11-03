"""Build preference-aware searches on public job and internship portals."""

import re
from typing import Dict, List
from urllib.parse import urlencode


def _location_region(location: str) -> str:
    value = (location or "").casefold()
    tokens = set(re.findall(r"[a-z]+", value))
    if "india" in tokens:
        return "india"
    if "usa" in tokens or "us" in tokens or {"united", "states"}.issubset(tokens):
        return "united_states"
    if {"united", "kingdom"}.issubset(tokens) or "uk" in tokens or "britain" in tokens:
        return "united_kingdom"
    if "canada" in value:
        return "canada"
    if "australia" in value:
        return "australia"
    return "global"


def build_job_portals(
    role: str,
    location: str,
    opportunity_type: str = "Any",
    work_preference: str = "Any",
) -> List[Dict[str, str]]:
    """Create portal search links from the user's role and job preferences."""
    role = role.strip()
    location = location.strip()
    terms = [role]
    if opportunity_type != "Any":
        terms.append(opportunity_type)
    if work_preference != "Any":
        terms.append(work_preference)
    search_terms = " ".join(terms)

    linkedin_query = urlencode({"keywords": search_terms, "location": location})
    indeed_query = urlencode({"q": search_terms, "l": location})
    region = _location_region(location)
    indeed_hosts = {
        "india": "https://in.indeed.com/jobs",
        "united_states": "https://www.indeed.com/jobs",
        "united_kingdom": "https://uk.indeed.com/jobs",
        "canada": "https://ca.indeed.com/jobs",
        "australia": "https://au.indeed.com/jobs",
        "global": "https://www.indeed.com/jobs",
    }

    portals: List[Dict[str, str]] = [
        {
            "name": "LinkedIn Jobs",
            "url": f"https://www.linkedin.com/jobs/search/?{linkedin_query}",
            "action": "Search on LinkedIn",
            "description": "Role and location are prefilled. Refine experience level, date posted, and work type on LinkedIn.",
        },
        {
            "name": "Indeed",
            "url": f"{indeed_hosts[region]}?{indeed_query}",
            "action": "Search on Indeed",
            "description": "Open a role and location search on Indeed; review each employer's listing and application details.",
        },
    ]

    if opportunity_type == "Internship":
        if region == "india":
            role_terms = role.casefold()
            categories = [
                ("data science", ("data scientist", "data analyst", "data science", "machine learning", " ml ")),
                ("computer science", ("python", "software", "developer", "engineering", "ai", "ml", "data", "tech")),
                ("digital marketing", ("marketing", "seo", "social media")),
                ("finance", ("finance", "accounting", "investment")),
                ("graphic design", ("design", "ui", "ux", "graphic")),
                ("content writing", ("writing", "writer", "content", "editorial")),
                ("hr", ("human resources", " hr ", "recruiting", "talent")),
            ]
            category = next(
                (slug for slug, matches in categories if any(term in f" {role_terms} " for term in matches)),
                None,
            )
            internshala_url = "https://internshala.com/internships/"
            if category:
                internshala_url += f"{category.replace(' ', '-')}-internship/"
            portals.extend([
                {
                    "name": "Internshala",
                    "url": internshala_url,
                    "action": "Browse on Internshala",
                    "description": "India internship search, narrowed to a related field when possible. Set your city and work-from-home filter on the site.",
                },
                {
                    "name": "AICTE Internship Portal",
                    "url": "https://internship.aicte-india.org/",
                    "action": "Browse AICTE internships",
                    "description": "India's national internship portal. Search by your role or skills and check location and eligibility on each listing.",
                },
                {
                    "name": "Digital India Internship Portal",
                    "url": "https://dii.nic.in/",
                    "action": "Browse Digital India internships",
                    "description": "Check current Digital India internship openings, role details, location, and eligibility on the official portal.",
                },
                {
                    "name": "Unstop",
                    "url": "https://unstop.com/internships",
                    "action": "Browse on Unstop",
                    "description": "Student internships and early-career opportunities. Search your role and refine the listings on Unstop.",
                },
            ])
        elif region == "united_states":
            portals.extend([
                {
                    "name": "Handshake",
                    "url": "https://joinhandshake.com/students/",
                    "action": "Browse on Handshake",
                    "description": "Student and early-career roles; listing access may depend on your school account.",
                },
                {
                    "name": "USAJOBS Student Internships",
                    "url": "https://intern.usajobs.gov/search/results/",
                    "action": "Search USAJOBS internships",
                    "description": "Official U.S. federal internship listings. Search by role and review location and eligibility requirements.",
                },
            ])

    return portals


