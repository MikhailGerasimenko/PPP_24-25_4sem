from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database.database import Base

class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    
    books = relationship("Book", back_populates="author", cascade="all, delete")

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    year = Column(Integer)
    author_id = Column(Integer, ForeignKey("authors.id", ondelete="CASCADE"))
    
    author = relationship("Author", back_populates="books") 