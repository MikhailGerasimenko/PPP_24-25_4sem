from datetime import datetime
from pydantic import BaseModel, validator

class AuthorBase(BaseModel):
    name: str

class AuthorCreate(AuthorBase):
    pass

class Author(AuthorBase):
    id: int

    class Config:
        from_attributes = True

class BookBase(BaseModel):
    title: str
    year: int
    author_id: int

class BookCreate(BookBase):
    @validator('year')
    def validate_year(cls, v):
        current_year = datetime.now().year
        if v > current_year:
            raise ValueError(f'Год не может быть больше текущего ({current_year})')
        return v

class Book(BookBase):
    id: int

    class Config:
        from_attributes = True 