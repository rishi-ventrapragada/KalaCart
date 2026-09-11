from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Any
from app.core.security import get_current_user
from app.models.academy import (
    CourseResponse,
    ProgressUpdateRequest,
    ProgressResponse,
    QuizSubmission,
    QuizResultResponse,
    CertificateResponse,
    AITutorQuery,
    AITutorResponse
)
from app.services.academy_service import AcademyService
from app.ai.academy_tutor import AITutorEngine

router = APIRouter(prefix="/api/v1/academy", tags=["AI Knowledge Academy"])

def _get_user_info(current_user: Any) -> tuple[str, str]:
    if isinstance(current_user, dict):
        uid = current_user.get("uid") or current_user.get("id", "artisan-anon")
        name = current_user.get("name") or current_user.get("full_name", "Artisan Scholar")
        return uid, name
    uid = getattr(current_user, "id", getattr(current_user, "uid", "artisan-anon"))
    name = getattr(current_user, "full_name", getattr(current_user, "name", "Artisan Scholar"))
    return uid, name

@router.get("/courses", response_model=List[CourseResponse])
def list_courses(current_user: Any = Depends(get_current_user)):
    """
    List all academy courses with personal completion progress.
    """
    uid, _ = _get_user_info(current_user)
    return AcademyService.list_courses(user_id=uid)

@router.get("/courses/{course_id}", response_model=CourseResponse)
def get_course(course_id: str, current_user: Any = Depends(get_current_user)):
    """
    Get detailed course curriculum, video stream links, offline downloadable PDFs, and quiz items.
    """
    uid, _ = _get_user_info(current_user)
    course = AcademyService.get_course(course_id=course_id, user_id=uid)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.post("/courses/{course_id}/progress", response_model=ProgressResponse)
def update_lesson_progress(
    course_id: str,
    payload: ProgressUpdateRequest,
    current_user: Any = Depends(get_current_user)
):
    """
    Mark a lesson as completed and sync cross-device course progress.
    """
    uid, _ = _get_user_info(current_user)
    try:
        return AcademyService.update_progress(
            user_id=uid,
            course_id=course_id,
            completed_lesson_id=payload.completed_lesson_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/courses/{course_id}/quiz", response_model=QuizResultResponse)
def submit_course_quiz(
    course_id: str,
    payload: QuizSubmission,
    current_user: Any = Depends(get_current_user)
):
    """
    Submit chapter quiz, grade score, and issue verified certificate if passed (>=70%).
    """
    uid, name = _get_user_info(current_user)
    try:
        return AcademyService.submit_quiz(
            user_id=uid,
            user_name=name,
            course_id=course_id,
            submission=payload
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/certificates", response_model=List[CertificateResponse])
def list_certificates(current_user: Any = Depends(get_current_user)):
    """
    List all certificates earned by the artisan.
    """
    uid, _ = _get_user_info(current_user)
    return AcademyService.list_certificates(user_id=uid)

@router.post("/tutor/ask", response_model=AITutorResponse)
def ask_ai_tutor(query: AITutorQuery):
    """
    Ask AI Knowledge Tutor questions in regional Indian languages (Hindi, Tamil, Telugu, Bengali, English).
    """
    return AITutorEngine.answer_query(query=query)
