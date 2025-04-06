from sqlalchemy import Column, Integer, String, Text
from app.db.database import Base

class Lesson(Base):
    __tablename__ = "lessons"
    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, index=True)
    difficulty = Column(String)
    mdx_content = Column(Text)
