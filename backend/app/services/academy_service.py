from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from app.models.academy import (
    CourseResponse,
    LessonResponse,
    QuizQuestion,
    ProgressResponse,
    QuizSubmission,
    QuizResultResponse,
    CertificateResponse
)

# Seeded Master Courses with Lessons and Quizzes
_SEED_COURSES = [
    {
        "id": "course-photo-01",
        "slug": "product-photography-for-artisans",
        "title": "Mastering Natural Product Photography with Smartphones",
        "description": "Learn to capture studio-quality photos of handicrafts using natural sunlight, rustic backgrounds, and smartphone cameras.",
        "category": "Photography",
        "thumbnail_url": "https://storage.kalacart.in/academy/thumbs/photo_masterclass.jpg",
        "duration_minutes": 45,
        "lesson_count": 3,
        "difficulty_level": "Beginner",
        "lessons": [
            {
                "id": "lesson-photo-01",
                "course_id": "course-photo-01",
                "title": "Lighting Secrets: Golden Hour & Diffused Window Light",
                "sequence_order": 1,
                "video_url": "https://storage.kalacart.in/academy/videos/photo_lighting.mp4",
                "video_duration_seconds": 600,
                "pdf_url": "https://storage.kalacart.in/academy/guides/photo_lighting_guide.pdf",
                "pdf_size_bytes": 1450000,
                "summary_text": "Understand how 45-degree angle window light brings out textures on clay and textiles.",
                "is_completed": False
            },
            {
                "id": "lesson-photo-02",
                "course_id": "course-photo-01",
                "title": "Framing, Angles & Multi-Shot Showcase",
                "sequence_order": 2,
                "video_url": "https://storage.kalacart.in/academy/videos/photo_framing.mp4",
                "video_duration_seconds": 720,
                "pdf_url": "https://storage.kalacart.in/academy/guides/photo_angles_cheat_sheet.pdf",
                "pdf_size_bytes": 1200000,
                "summary_text": "Master front, top-down flat lay, close-up texture, and lifestyle scale shots.",
                "is_completed": False
            },
            {
                "id": "lesson-photo-03",
                "course_id": "course-photo-01",
                "title": "Color Correction & Background Clean-up",
                "sequence_order": 3,
                "video_url": "https://storage.kalacart.in/academy/videos/photo_editing.mp4",
                "video_duration_seconds": 540,
                "pdf_url": "https://storage.kalacart.in/academy/guides/photo_editing_steps.pdf",
                "pdf_size_bytes": 980000,
                "summary_text": "Preserve natural dye shades and remove background blemishes without distorting authenticity.",
                "is_completed": False
            }
        ],
        "quiz": [
            {
                "question_id": "q-photo-1",
                "question_text": "Which lighting is best for photographing handmade pottery?",
                "options": ["Direct harsh camera flash", "Diffused morning sunlight near a window", "Dark room with flashlight", "Fluorescent ceiling bulb"],
                "correct_option_index": 1,
                "explanation": "Diffused morning natural light highlights textures without causing harsh glaze glare."
            },
            {
                "question_id": "q-photo-2",
                "question_text": "Why should you include a close-up macro shot in your catalog?",
                "options": ["To hide flaws", "To show intricate hand-weaving or brushwork details", "To blur the background", "To reduce image file size"],
                "correct_option_index": 1,
                "explanation": "Close-up macro shots establish authentic handcrafted value to discerning buyers."
            }
        ]
    },
    {
        "id": "course-price-02",
        "slug": "profitable-pricing-and-costing",
        "title": "Artisan Pricing Matrix: Profit, Labor & B2B Wholesale",
        "description": "Never sell at a loss. Calculate material costs, hourly artisan wages, overheads, and healthy wholesale margins.",
        "category": "Pricing",
        "thumbnail_url": "https://storage.kalacart.in/academy/thumbs/pricing_masterclass.jpg",
        "duration_minutes": 60,
        "lesson_count": 2,
        "difficulty_level": "Intermediate",
        "lessons": [
            {
                "id": "lesson-price-01",
                "course_id": "course-price-02",
                "title": "Cost Baselines & Calculating Hourly Craft Labor",
                "sequence_order": 1,
                "video_url": "https://storage.kalacart.in/academy/videos/costing_formula.mp4",
                "video_duration_seconds": 800,
                "pdf_url": "https://storage.kalacart.in/academy/guides/costing_worksheet.pdf",
                "pdf_size_bytes": 850000,
                "summary_text": "Add up raw materials, firing kiln costs, hourly wages, and packaging to find your cost floor.",
                "is_completed": False
            },
            {
                "id": "lesson-price-02",
                "course_id": "course-price-02",
                "title": "Tiered Pricing for Retail vs Bulk B2B Orders",
                "sequence_order": 2,
                "video_url": "https://storage.kalacart.in/academy/videos/tiered_pricing.mp4",
                "video_duration_seconds": 950,
                "pdf_url": "https://storage.kalacart.in/academy/guides/b2b_wholesale_matrix.pdf",
                "pdf_size_bytes": 1100000,
                "summary_text": "Structuring 10%, 20%, and 30% discount tiers without eroding minimum gross margin.",
                "is_completed": False
            }
        ],
        "quiz": [
            {
                "question_id": "q-price-1",
                "question_text": "What is the primary factor that must NEVER be excluded from craft cost calculations?",
                "options": ["Artisan labor hours and fair wages", "Buyer's budget", "Competitor price", "Discount coupons"],
                "correct_option_index": 0,
                "explanation": "Fair labor hours must always be compensated to ensure sustainable livelihood."
            }
        ]
    }
]

# In-Memory Store for user progress and certificates
_USER_PROGRESS: Dict[str, Dict[str, Any]] = {}
_QUIZ_RESULTS: List[Dict[str, Any]] = []
_CERTIFICATES: Dict[str, Dict[str, Any]] = {}

class AcademyService:
    @staticmethod
    def list_courses(user_id: str) -> List[CourseResponse]:
        results = []
        for c in _SEED_COURSES:
            key = f"{user_id}_{c['id']}"
            prog = _USER_PROGRESS.get(key)
            completed_ids = prog["completed_lesson_ids"] if prog else []
            perc = prog["completion_percentage"] if prog else 0.0
            is_comp = prog["is_completed"] if prog else False

            lessons = []
            for l in c["lessons"]:
                l_copy = dict(l)
                l_copy["is_completed"] = l["id"] in completed_ids
                lessons.append(LessonResponse(**l_copy))

            results.append(CourseResponse(
                id=c["id"],
                slug=c["slug"],
                title=c["title"],
                description=c["description"],
                category=c["category"],
                thumbnail_url=c["thumbnail_url"],
                duration_minutes=c["duration_minutes"],
                lesson_count=c["lesson_count"],
                difficulty_level=c["difficulty_level"],
                completion_percentage=perc,
                is_completed=is_comp,
                lessons=lessons,
                quiz=[QuizQuestion(**q) for q in c.get("quiz", [])]
            ))
        return results

    @staticmethod
    def get_course(course_id: str, user_id: str) -> Optional[CourseResponse]:
        for c in _SEED_COURSES:
            if c["id"] == course_id or c["slug"] == course_id:
                key = f"{user_id}_{c['id']}"
                prog = _USER_PROGRESS.get(key)
                completed_ids = prog["completed_lesson_ids"] if prog else []
                perc = prog["completion_percentage"] if prog else 0.0
                is_comp = prog["is_completed"] if prog else False

                lessons = []
                for l in c["lessons"]:
                    l_copy = dict(l)
                    l_copy["is_completed"] = l["id"] in completed_ids
                    lessons.append(LessonResponse(**l_copy))

                return CourseResponse(
                    id=c["id"],
                    slug=c["slug"],
                    title=c["title"],
                    description=c["description"],
                    category=c["category"],
                    thumbnail_url=c["thumbnail_url"],
                    duration_minutes=c["duration_minutes"],
                    lesson_count=c["lesson_count"],
                    difficulty_level=c["difficulty_level"],
                    completion_percentage=perc,
                    is_completed=is_comp,
                    lessons=lessons,
                    quiz=[QuizQuestion(**q) for q in c.get("quiz", [])]
                )
        return None

    @staticmethod
    def update_progress(user_id: str, course_id: str, completed_lesson_id: str) -> ProgressResponse:
        course = None
        for c in _SEED_COURSES:
            if c["id"] == course_id:
                course = c
                break
        if not course:
            raise ValueError("Course not found")

        key = f"{user_id}_{course_id}"
        prog = _USER_PROGRESS.get(key, {
            "course_id": course_id,
            "user_id": user_id,
            "completed_lesson_ids": [],
            "completion_percentage": 0.0,
            "is_completed": False,
            "last_accessed_at": datetime.utcnow().isoformat()
        })

        if completed_lesson_id not in prog["completed_lesson_ids"]:
            prog["completed_lesson_ids"].append(completed_lesson_id)

        total_lessons = len(course["lessons"])
        pct = round((len(prog["completed_lesson_ids"]) / total_lessons) * 100.0, 2)
        prog["completion_percentage"] = min(pct, 100.0)
        prog["is_completed"] = len(prog["completed_lesson_ids"]) >= total_lessons
        prog["last_accessed_at"] = datetime.utcnow().isoformat()

        _USER_PROGRESS[key] = prog
        return ProgressResponse(**prog)

    @staticmethod
    def submit_quiz(user_id: str, user_name: str, course_id: str, submission: QuizSubmission) -> QuizResultResponse:
        course = None
        for c in _SEED_COURSES:
            if c["id"] == course_id:
                course = c
                break
        if not course:
            raise ValueError("Course not found")

        quiz_items = course.get("quiz", [])
        if not quiz_items:
            raise ValueError("No quiz configured for this course")

        # Grade answers
        correct_count = 0
        answer_map = {a.question_id: a.selected_option_index for a in submission.answers}
        for q in quiz_items:
            if answer_map.get(q["question_id"]) == q["correct_option_index"]:
                correct_count += 1

        total_q = len(quiz_items)
        percentage = round((correct_count / total_q) * 100.0, 2)
        passed = percentage >= 70.0

        certificate = None
        if passed:
            cert_id = str(uuid.uuid4())
            cert_number = f"KC-ACAD-{datetime.utcnow().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"
            now = datetime.utcnow().isoformat()
            
            cert_record = {
                "id": cert_id,
                "user_id": user_id,
                "course_id": course_id,
                "certificate_number": cert_number,
                "recipient_name": user_name,
                "course_title": course["title"],
                "issue_date": now,
                "certificate_pdf_url": f"https://storage.kalacart.in/certificates/{cert_number}.pdf",
                "verification_qr_url": f"https://kalacart.in/verify/cert/{cert_number}"
            }
            _CERTIFICATES[cert_id] = cert_record
            certificate = CertificateResponse(**cert_record)

        return QuizResultResponse(
            course_id=course_id,
            score=correct_count,
            total_questions=total_q,
            percentage=percentage,
            passed=passed,
            certificate=certificate
        )

    @staticmethod
    def list_certificates(user_id: str) -> List[CertificateResponse]:
        return [
            CertificateResponse(**c)
            for c in _CERTIFICATES.values()
            if c["user_id"] == user_id
        ]
