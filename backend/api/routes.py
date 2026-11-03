import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from backend.api.auth import get_current_user

from backend.models.schemas import AnalysisResponse, ComponentScores, JDComparison, SkillValidationDetails

from backend.utils.file_utils import (
    get_default_grammar_results,
    get_default_location_results,
    get_default_skill_validation_results,
)

logger = logging.getLogger('ats_resume_scorer')

router = APIRouter(prefix='/api/v1', tags=['Analysis'])


def _clean(text: str) -> str:
    for prefix in ('✅', '🌟', '❌', '⚠️', '📝', '🔴', '🟡', '🟢', '🟠', '👍'):
        text = text.lstrip(prefix)
    return text.strip()


@router.post('/analyze-resume', response_model=AnalysisResponse)
async def analyze_resume(
    request: Request,
    resume: UploadFile = File(..., description='Resume file - PDF or DOCX, max 5MB'),
    job_description: str = Form('', description='Job description text(optional)'),
    user_id: str = Depends(get_current_user),
):
    logger.warning('Received analyze-resume request')
    warnings: List[str] = []

    nlp = request.app.state.nlp
    embedder = request.app.state.embedder

    try:
        logger.warning('Reading uploaded resume')
        file_bytes = resume.file.read()
        filename = resume.filename or 'resume'
        logger.warning("Read uploaded resume '%s' (%s bytes)", filename, len(file_bytes))

        logger.warning('Importing resume parser')
        from backend.services.resume_parser import (
            FileParsingError,
            FileValidationError,
            parse_resume_file,
        )

        logger.warning('Resume parser imported')
        logger.warning("Parsing uploaded resume '%s'", filename)
        resume_text, _metadata = await run_in_threadpool(parse_resume_file, file_bytes, filename)
        logger.warning("Parsed '%s': %s chars extracted", filename, len(resume_text))

    except Exception as exc:
        logger.error(f'File Parsing Falied: {exc}')
        raise HTTPException(
            status_code=422,
            detail=f'Could not read or parse the resume: {exc}'
        )
    
    #Full Analysis Pipeline

    try:
        from backend.services.resume_analyzer import analyze_full_resume

        logger.warning("Starting analysis pipeline for '%s'", filename)
        result = await run_in_threadpool(
            analyze_full_resume,
            resume_text=resume_text,
            nlp=nlp,
            embedder=embedder,
            job_description=job_description,
        )
        logger.warning("Analysis pipeline completed for '%s'", filename)

    except Exception as exc:
        logger.exception('Full Analysis Pipeline Failed')
        raise HTTPException(status_code=500, detail=f'Analysis Pipeline: {exc}')

    jd_comparison_result = None
    if result.get('jd_comparison'):
        jd_comparison_result = JDComparison(
            match_percentage=round(float(result['jd_comparison'].get('match_percentage', 0.0)), 1),
            semantic_similarity=round(float(result['jd_comparison'].get('semantic_similarity', 0.0)), 3),
            matched_keywords=result['jd_comparison'].get('matched_keywords', [])[:20],
            missing_keywords=result['jd_comparison'].get('missing_keywords', [])[:15],
            skills_gap=result['jd_comparison'].get('skills_gap', [])[:10],
        )

    # Skill validation is available for resume-only scans as well as JD scans.
    svd_raw = result.get('skill_validation_details') or {}
    skill_val_details = SkillValidationDetails(
        validated=svd_raw.get('validated', []),
        unvalidated=svd_raw.get('unvalidated', []),
        total=svd_raw.get('total', 0),
        validated_count=svd_raw.get('validated_count', 0),
        validation_pct=svd_raw.get('validation_pct', 0.0),
    )

    response = AnalysisResponse(
        ATS_score=result['ats_score'],
        component_scores=ComponentScores(**result['component_scores']),
        issues_summary=result['issues_summary'],
        detailed_feedback=result.get('detailed_feedback', []),
        strengths=result.get('strengths', []),
        jd_match_analysis=jd_comparison_result,
        skill_validation_details=skill_val_details,

        #Retro-Compatibility Fields
        ats_score=result['ats_score'],
        keyword_match=jd_comparison_result.match_percentage if jd_comparison_result else 0.0,
        missing_keywords=result.get('missing_keywords', []),
        matched_keywords=result.get('matched_keywords', []),
        skills=list(result.get('skills', [])[:20]),
        jd_comparison=jd_comparison_result,
        interpretation=result.get('interpretation', ''),
    )

    if user_id and user_id.strip():
        try:
            from backend.database.supabase_db import save_analysis
            await save_analysis(user_id.strip(), filename, result)
        except Exception as exc:
            logger.warning(f'History Save Failed (non-blocking): {exc}')

    return response


@router.get('/health')
async def health_check(request: Request):
    """Health check - confirms models are loaded and the API is ready."""
    return {
        'status': 'healthy',
        'nlp_loaded': request.app.state.nlp is not None,
        'embedder_loaded': request.app.state.embedder is not None,
    }


@router.get('/history')
async def get_history(user_id: str = Depends(get_current_user)):
    """
    Retrieve all Past analysis results for a user.
    The User ID is sent via the USER-ID header (set by the frontend).
    """
    from backend.database.supabase_db import get_user_history
    try:
        history = await get_user_history(user_id)
        return history
    except Exception as exc:
        logger.error(f'History Fetch Falied: {exc}')
        raise HTTPException(status_code=500, detail=f'Could Not Load History: {exc}')


@router.delete('/history/{analysis_id}')
async def delete_history_entry(
    analysis_id: str,
    user_id: str = Depends(get_current_user),
):
    """
    Delete a Specific analysis from the user's history.
    """
    from backend.database.supabase_db import delete_analysis
    try:
        success = await delete_analysis(analysis_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail='Analysis not found or not owned by this user.')

        return {'status': 'deleted', 'id': analysis_id}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f'History delete failed: {exc}')
        raise HTTPException(status_code=500, detail=f'Could Not delete: {exc}')


@router.post('/generate-pdf')
async def generate_pdf(
    data: AnalysisResponse,
    user_id: str = Depends(get_current_user),
):
    from backend.services.report_generator import generate_html_reports
    from backend.services.pdf_export import generate_combined_pdf
    from fastapi.responses import Response
    from starlette.concurrency import run_in_threadpool

    try:
        html_docs = generate_html_reports(data.model_dump())
        pdf_bytes = await run_in_threadpool(generate_combined_pdf, html_docs)

        return Response(
            content=pdf_bytes,
            media_type='application/pdf',
            headers={
                'Content-Disposition': 'attachment; filename=ats_report.pdf',
            },
        )
    except Exception as e:
        logger.error(f'Failed to Generate PDF: {e}')
        raise HTTPException(status_code=500, detail=f'Failed to Generate PDF: {e}')


@router.get('/history/{analysis_id}/pdf')
async def generate_history_pdf(
    analysis_id: str,
    user_id: str = Depends(get_current_user),
):
    from backend.database.supabase_db import get_user_history
    from backend.services.report_generator import generate_html_reports
    from backend.services.pdf_export import generate_combined_pdf
    from fastapi.responses import Response
    from starlette.concurrency import run_in_threadpool

    history = await get_user_history(user_id)
    analysis_data = next((item['analysis_result'] for item in history if item['id'] == analysis_id), None)

    if not analysis_data:
        raise HTTPException(status_code=404, detail='Analysis Not Found')

    try:
        html_docs = generate_html_reports(analysis_data)
        pdf_bytes = await run_in_threadpool(generate_combined_pdf, html_docs)

        return Response(
            content=pdf_bytes,
            media_type='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename=ats_report_{analysis_id}.pdf',
            },
        )
    except Exception as e:
        logger.error(f'Falied To Generate PDF for History: {e}')
        raise HTTPException(status_code=500, detail=f'Failed to Generate PDF: {e}')

@router.get('/')
async def root():
    return {
        'name': 'ATS Resume Scorer API',
        'version': '2.0.0',
        'endpoints': {
            'POST /api/v1/analyze-resume': 'Analyze a resume.',
            'GET /api/v1/history': 'Get user history.',
            'DELETE /api/v1/history/:id': 'Delete a History Entry.',
            'GET /api/v1/Health': 'Health Check.',
            'POST /api/v1/generate-pdf': 'Generate PDF Report From Data.',
        }
    }

