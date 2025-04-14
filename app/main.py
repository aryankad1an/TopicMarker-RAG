from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from app.routers import rag
from app.services.vectorstore import init_pinecone
from app.utils.response import error_response  # Make sure this file exists

app = FastAPI(title="Lesson Plan RAG Backend")

@app.on_event("startup")
async def startup_event():
    init_pinecone()


# '/' ROUTE 
@app.get("/")
async def root():
    return {"message": "Welcome to the Lesson Plan RAG Backend!"}


# Include RAG routes
app.include_router(rag.router, prefix="/rag", tags=["RAG"])


# ✅ Global exception handlers

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return error_response(
        message="Internal server error",
        status_code=500,
        details=str(exc)
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return error_response(
        message="Validation error",
        status_code=422,
        details=exc.errors()
    )
