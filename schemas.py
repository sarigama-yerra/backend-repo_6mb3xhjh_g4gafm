"""
Database Schemas for RightTick

Each Pydantic model below represents a MongoDB collection.
Collection name is the lowercase of the class name.
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

# Core entities
class Student(BaseModel):
    name: str
    student_id: str = Field(..., description="Institute roll / registration number")
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    integrity_score: float = Field(100, ge=0, le=100)

class Test(BaseModel):
    title: str
    code: str = Field(..., description="Join code shared with students")
    duration_minutes: int = Field(..., ge=5, le=300)
    subject: Optional[str] = None
    status: Literal["upcoming", "ongoing", "completed"] = "upcoming"

class Question(BaseModel):
    test_code: str
    qtype: Literal["mcq", "coding", "theory"]
    title: str
    prompt: str
    options: Optional[List[str]] = None
    answer: Optional[str] = None
    difficulty: Optional[Literal["easy", "medium", "hard"]] = None
    topic: Optional[str] = None

class Submission(BaseModel):
    test_code: str
    student_id: str
    answers: dict = Field(default_factory=dict)
    code: Optional[str] = None
    score: Optional[float] = None
    coding_accuracy: Optional[float] = None

class Alert(BaseModel):
    test_code: str
    student_id: str
    kind: Literal["eye_movement", "tab_change", "keyboard_toggle", "face_missing", "other"]
    severity: Literal["low", "medium", "high"] = "low"
    message: str
    snapshot_url: Optional[str] = None

# Optional analytics shape (stored if needed)
class IntegrityMetric(BaseModel):
    test_code: str
    student_id: str
    score: float = Field(..., ge=0, le=100)
