from fastapi import FastAPI
from app.routers import lessons
from app.db import database

app = FastAPI(title="Lesson Generator API")

# Include lesson routes
app.include_router(lessons.router)

# Initialize the database
database.init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
