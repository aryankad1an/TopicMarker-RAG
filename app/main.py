from fastapi import FastAPI
from app.routers import rag
from app.services.vectorstore import init_pinecone

app = FastAPI(title="Lesson Plan RAG Backend")

@app.on_event("startup")
async def startup_event():
    init_pinecone()


# '/' ROUTE 
@app.get("/")
async def root():
    return {"message": "Welcome to the Lesson Plan RAG Backend!"}


app.include_router(rag.router, prefix="/rag", tags=["RAG"])