import os
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import Student, Test as TestSchema, Question, Submission, Alert

app = FastAPI(title="RightTick API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "RightTick backend is running"}

# Health and DB check
@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Connected"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = getattr(db, "name", None) or os.getenv("DATABASE_NAME") or "Unknown"
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()[:20]
            except Exception as e:
                response["database"] = f"⚠️ Connected but error listing collections: {str(e)[:60]}"
        else:
            response["database"] = "⚠️ Database not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# Simple DTOs
class CreateTestRequest(BaseModel):
    title: str
    code: str
    duration_minutes: int
    subject: Optional[str] = None

class AddQuestionsRequest(BaseModel):
    test_code: str
    questions: List[Question]

class AssignStudentsRequest(BaseModel):
    test_code: str
    students: List[Student]

# Admin endpoints
@app.post("/admin/tests")
def create_test(payload: CreateTestRequest):
    test = TestSchema(title=payload.title, code=payload.code, duration_minutes=payload.duration_minutes, subject=payload.subject)
    inserted_id = create_document("test", test)
    return {"ok": True, "id": inserted_id}

@app.post("/admin/tests/questions")
def add_questions(payload: AddQuestionsRequest):
    ids = []
    for q in payload.questions:
        ids.append(create_document("question", q))
    return {"ok": True, "count": len(ids), "ids": ids}

@app.post("/admin/tests/assign")
def assign_students(payload: AssignStudentsRequest):
    ids = []
    for s in payload.students:
        ids.append(create_document("student", s))
    return {"ok": True, "count": len(ids)}

@app.get("/admin/tests")
def list_tests():
    items = get_documents("test")
    # convert ObjectId to string
    for it in items:
        it["_id"] = str(it["_id"])
    return {"ok": True, "items": items}

# Student endpoints
class JoinTestRequest(BaseModel):
    name: str
    student_id: str
    test_code: str

@app.post("/student/join")
def student_join(payload: JoinTestRequest):
    student = Student(name=payload.name, student_id=payload.student_id)
    # upsert-like: for demo, just create a doc per join event
    sid = create_document("student", student)
    return {"ok": True, "student_doc": sid}

@app.get("/student/questions/{test_code}")
def get_questions(test_code: str):
    qs = get_documents("question", {"test_code": test_code})
    for q in qs:
        q["_id"] = str(q["_id"])
        # never send correct answer to client directly for MCQ in real prod
    return {"ok": True, "items": qs}

class SubmitRequest(BaseModel):
    test_code: str
    student_id: str
    answers: dict = {}
    code: Optional[str] = None

@app.post("/student/submit")
def submit_answers(payload: SubmitRequest):
    sub = Submission(test_code=payload.test_code, student_id=payload.student_id, answers=payload.answers, code=payload.code)
    sid = create_document("submission", sub)
    return {"ok": True, "submission_id": sid}

# Proctor alerts
@app.post("/alerts")
def push_alert(alert: Alert):
    aid = create_document("alert", alert)
    return {"ok": True, "alert_id": aid}

@app.get("/alerts/{test_code}")
def list_alerts(test_code: str):
    items = get_documents("alert", {"test_code": test_code})
    for it in items:
        it["_id"] = str(it["_id"])
    return {"ok": True, "items": items}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
