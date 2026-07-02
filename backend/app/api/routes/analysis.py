from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import DocumentParseError, NotFoundError
from app.db.database import get_db
from app.db.models import AnalysisRecord
from app.models.schemas import AnalysisResult, AnalysisSummary
from app.services.orchestrator import run_analysis
from app.services.parsing.document_parser import parse_document

router = APIRouter(prefix="/api", tags=["analysis"])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


@router.post("/analyze", response_model=AnalysisResult)
async def analyze(
    resume: UploadFile = File(...),
    job_description: str = Form(default=""),
    jd_file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
) -> AnalysisResult:
    resume_bytes = await resume.read()
    if len(resume_bytes) > MAX_UPLOAD_BYTES:
        raise DocumentParseError("Resume file exceeds the 10 MB limit.")

    jd_text = job_description.strip()
    if not jd_text and jd_file is not None:
        jd_bytes = await jd_file.read()
        jd_text = parse_document(jd_file.filename or "jd.txt", jd_bytes).text
    if not jd_text:
        raise DocumentParseError("Provide a job description (text or file).")

    result = run_analysis(resume.filename or "resume", resume_bytes, jd_text)

    db.add(AnalysisRecord(
        id=result.id,
        created_at=result.created_at,
        resume_filename=result.meta.resume_filename,
        overall_match=result.scores.overall_match,
        ats_score_pct=round(100.0 * result.ats.total_score / result.ats.max_score, 1),
        result=result.model_dump(mode="json"),
    ))
    db.commit()
    return result


@router.get("/analyses", response_model=list[AnalysisSummary])
def list_analyses(db: Session = Depends(get_db)) -> list[AnalysisSummary]:
    rows = db.scalars(
        select(AnalysisRecord).order_by(AnalysisRecord.created_at.desc()).limit(50)
    ).all()
    return [
        AnalysisSummary(
            id=r.id, created_at=r.created_at, resume_filename=r.resume_filename,
            overall_match=r.overall_match, ats_score_pct=r.ats_score_pct,
        )
        for r in rows
    ]


@router.get("/analyses/{analysis_id}", response_model=AnalysisResult)
def get_analysis(analysis_id: str, db: Session = Depends(get_db)) -> AnalysisResult:
    row = db.get(AnalysisRecord, analysis_id)
    if row is None:
        raise NotFoundError(f"Analysis '{analysis_id}' not found.")
    return AnalysisResult.model_validate(row.result)
