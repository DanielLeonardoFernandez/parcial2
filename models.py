from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship
from pydantic import validator
import re

# Tabla intermedia para relación muchos a muchos
class BookAuthorLink(SQLModel, table=True):
    book_id: Optional[int] = Field(default=None, foreign_key="book.id", primary_key=True)
    author_id: Optional[int] = Field(default=None, foreign_key="author.id", primary_key=True)


# -------------------------
#        MODELO AUTHOR
# -------------------------
class AuthorBase(SQLModel):
    name: str = Field(..., min_length=1, max_length=150)
    country: Optional[str] = Field(default=None, max_length=100)
    birth_year: Optional[int] = Field(default=None, ge=0, le=9999)


class Author(AuthorBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    is_active: bool = Field(default=True, nullable=False)

    books: List["Book"] = Relationship(back_populates="authors", link_model=BookAuthorLink)


class AuthorCreate(AuthorBase):
    pass


class AuthorRead(AuthorBase):
    id: int
    is_active: bool


# -------------------------
#        MODELO BOOK
# -------------------------
class BookBase(SQLModel):
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


class Book(BookBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    is_active: bool = Field(default=True, nullable=False)

    authors: List[Author] = Relationship(back_populates="books", link_model=BookAuthorLink)


class BookCreate(BookBase):
    author_ids: Optional[List[int]] = []


class BookRead(BookBase):
    id: int
    is_active: bool
    authors: List[AuthorRead] = []
