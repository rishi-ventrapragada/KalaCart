from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class LessonResponse(BaseModel):
    id: str
    course_id: str
    title: str
    sequence_order: int
    video_url: str
    video_duration_seconds: int
    pdf_url: Optional[str] = None
    pdf_size_bytes: Optional[int] = 0
    summary_text: str
    is_completed: bool = False

class QuizQuestion(BaseModel):
    question_id: str
    question_text: str
    options: List[str]
    correct_option_index: int
    explanation: str

class CourseResponse(BaseModel):
    id: str
    slug: str
    title: str
    description: str
    category: str
    thumbnail_url: str
    duration_minutes: int
    lesson_count: int
    difficulty_level: str
    completion_percentage: float = 0.0
    is_completed: bool = False
    lessons: List[LessonResponse] = Field(default_factory=list)
    quiz: List[QuizQuestion] = Field(default_factory=list)

class ProgressUpdateRequest(BaseModel):
    completed_lesson_id: str

class ProgressResponse(BaseModel):
    course_id: str
    user_id: str
    completed_lesson_ids: List[str]
    completion_percentage: float
    is_completed: bool
    last_accessed_at: str

class QuizAnswerItem(BaseModel):
    question_id: str
    selected_option_index: int

class QuizSubmission(BaseModel):
    answers: List[QuizAnswerItem]

class CertificateResponse(BaseModel):
    id: str
    user_id: str
    course_id: str
    certificate_number: str
    recipient_name: str
    course_title: str
    issue_date: str
    certificate_pdf_url: str
    verification_qr_url: str

class QuizResultResponse(BaseModel):
    course_id: str
    score: int
    total_questions: int
    percentage: float
    passed: bool
    certificate: Optional[CertificateResponse] = None

class AITutorQuery(BaseModel):
    question: str
    course_id: Optional[str] = None
    preferred_language: str = "en"  # "hi", "ta", "te", "bn", "mr", "gu", "kn", "en"

class AITutorResponse(BaseModel):
    answer: str
    detected_language: str
    suggested_followups: List[str]
    reference_lesson_id: Optional[str] = None
