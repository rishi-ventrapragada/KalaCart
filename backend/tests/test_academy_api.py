from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.core.security import get_current_user

@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_user] = lambda: {
        "uid": "artisan-raghurajpur-001",
        "email": "laxman.patachitra@odisha.in",
        "name": "Laxman Maharana",
        "role": "seller"
    }
    yield
    app.dependency_overrides.clear()

def test_academy_course_progress_and_completion():
    client = TestClient(app)

    # 1. Fetch available courses
    res = client.get("/api/v1/academy/courses")
    assert res.status_code == 200
    courses = res.json()
    assert len(courses) >= 2
    photo_course = next(c for c in courses if c["id"] == "course-photo-01")
    assert photo_course["completion_percentage"] == 0.0
    assert not photo_course["is_completed"]

    # 2. Get course details
    res_details = client.get("/api/v1/academy/courses/course-photo-01")
    assert res_details.status_code == 200
    details = res_details.json()
    assert len(details["lessons"]) == 3
    assert len(details["quiz"]) == 2

    # 3. Mark lesson 1 completed
    res_prog1 = client.post("/api/v1/academy/courses/course-photo-01/progress", json={
        "completed_lesson_id": "lesson-photo-01"
    })
    assert res_prog1.status_code == 200
    prog1 = res_prog1.json()
    assert "lesson-photo-01" in prog1["completed_lesson_ids"]
    assert prog1["completion_percentage"] == 33.33

    # 4. Mark remaining lessons completed
    client.post("/api/v1/academy/courses/course-photo-01/progress", json={
        "completed_lesson_id": "lesson-photo-02"
    })
    res_prog3 = client.post("/api/v1/academy/courses/course-photo-01/progress", json={
        "completed_lesson_id": "lesson-photo-03"
    })
    assert res_prog3.status_code == 200
    prog3 = res_prog3.json()
    assert prog3["completion_percentage"] == 100.0
    assert prog3["is_completed"] is True

def test_quiz_submission_and_certificate_issuance():
    client = TestClient(app)

    # 1. Submit quiz with passing score (100%)
    quiz_submission = {
        "answers": [
            {"question_id": "q-photo-1", "selected_option_index": 1},
            {"question_id": "q-photo-2", "selected_option_index": 1}
        ]
    }
    res_quiz = client.post("/api/v1/academy/courses/course-photo-01/quiz", json=quiz_submission)
    assert res_quiz.status_code == 200
    result = res_quiz.json()
    assert result["score"] == 2
    assert result["percentage"] == 100.0
    assert result["passed"] is True
    assert result["certificate"] is not None
    cert = result["certificate"]
    assert cert["recipient_name"] == "Laxman Maharana"
    assert "KC-ACAD-" in cert["certificate_number"]

    # 2. Check certificates endpoint
    res_certs = client.get("/api/v1/academy/certificates")
    assert res_certs.status_code == 200
    certs = res_certs.json()
    assert any(c["certificate_number"] == cert["certificate_number"] for c in certs)

def test_multilingual_ai_tutor():
    client = TestClient(app)

    # English Photography Query
    res_en = client.post("/api/v1/academy/tutor/ask", json={
        "question": "How should I photograph terracotta pottery in sunlight?",
        "preferred_language": "en"
    })
    assert res_en.status_code == 200
    data_en = res_en.json()
    assert "sunlight" in data_en["answer"].lower()
    assert data_en["detected_language"] == "en"
    assert len(data_en["suggested_followups"]) > 0

    # Hindi Pricing Query
    res_hi = client.post("/api/v1/academy/tutor/ask", json={
        "question": "हस्तशिल्प की सही कीमत कैसे तय करें?",
        "preferred_language": "hi"
    })
    assert res_hi.status_code == 200
    data_hi = res_hi.json()
    assert "लागत" in data_hi["answer"] or "मुनाफा" in data_hi["answer"]
    assert data_hi["detected_language"] == "hi"

    # Tamil Packaging Query
    res_ta = client.post("/api/v1/academy/tutor/ask", json={
        "question": "மண்பாண்ட பேக்கிங் எப்படி செய்வது?",
        "preferred_language": "ta"
    })
    assert res_ta.status_code == 200
    data_ta = res_ta.json()
    assert data_ta["detected_language"] == "ta"
    assert len(data_ta["answer"]) > 0
