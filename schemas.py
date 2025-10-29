from typing import List, Optional
from pydantic import BaseModel, Field, validator
import re

# -------------------------
#       SCHEMAS AUTHOR
# -------------------------
class AuthorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    country: Optional[str] = Field(default=None, max_length=100)
    birth_year: Optional[int] = Field(default=None, ge=0, le=9999)


class AuthorCreate(AuthorBase):
    pass


class AuthorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    country: Optional[str] = Field(default=None, max_length=100)
    birth_year: Optional[int] = Field(default=None, ge=0, le=9999)


class AuthorRead(AuthorBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True


# -------------------------
#       SCHEMAS BOOK
# -------------------------
class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=250)
    isbn: str = Field(..., max_length=20)
    year_publication: Optional[int] = Field(default=None, ge=0, le=9999)
    copies_available: int = Field(default=1, ge=0)

    @validator("isbn")
    def isbn_format(cls, v):
        cleaned = re.sub(r"[^0-9]", "", v)
        if len(cleaned) not in (10, 13):
            raise ValueError("ISBN debe tener 10 o 13 dígitos (se permiten guiones)")
        return v


class BookCreate(BookBase):
    author_ids: Optional[List[int]] = []


class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=250)
    isbn: Optional[str] = Field(None, max_length=20)
    year_publication: Optional[int] = Field(None, ge=0, le=9999)
    copies_available: Optional[int] = Field(None, ge=0)
    author_ids: Optional[List[int]] = []

    @validator("isbn")
    def isbn_format(cls, v):
        if v is None:
            return v
        cleaned = re.sub(r"[^0-9]", "", v)
        if len(cleaned) not in (10, 13):
            raise ValueError("ISBN debe tener 10 o 13 dígitos (se permiten guiones)")
        return v


class BookRead(BookBase):
    id: int
    is_active: bool
    authors: List[AuthorRead] = []

    class Config:
        orm_mode = True


# -------------------------
#       SCHEMA BOOKAUTHORLINK (opcional)
# -------------------------
class BookAuthorLinkBase(BaseModel):
    book_id: int
    author_id: int


class BookAuthorLinkCreate(BookAuthorLinkBase):
    pass


class BookAuthorLinkRead(BookAuthorLinkBase):
    class Config:
        orm_mode = True
