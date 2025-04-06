from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from app.services import lesson_service

router = APIRouter(prefix="/lessons", tags=["Lessons"])

class LessonRequest(BaseModel):
    topic: str
    difficulty: str  # Expected values: easy, medium, advanced

@router.post("/", response_model=dict)
async def create_lesson(request: LessonRequest, background_tasks: BackgroundTasks):
    try:
        # Run the lesson generation process in the background
        background_tasks.add_task(lesson_service.generate_lesson, request.topic, request.difficulty)
        return {"message": "Lesson generation started. You can check the status later."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
