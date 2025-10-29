from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Optional

from db import get_session
from models import Book, BookCreate, BookRead, AuthorRead
import crud

router = APIRouter(prefix="/books", tags=["Books"])

# ---------------------------------------------------
# Crear un nuevo libro
# ---------------------------------------------------
@router.post("/", response_model=BookRead, status_code=201)
def create_book_endpoint(data: BookCreate, session: Session = Depends(get_session)):
    """
    Crear un nuevo libro y asociarlo con autores (author_ids en BookCreate).
    """
    book = Book.from_orm(data)
    return crud.create_book(session, book, data.author_ids or [])


# ---------------------------------------------------
# Listar libros activos (opcional: filtrar por año)
# ---------------------------------------------------
@router.get("/", response_model=List[BookRead])
def list_books_endpoint(
    year: Optional[int] = Query(None, description="Filtrar por año de publicación"),
    session: Session = Depends(get_session)
):
    """
    Listar todos los libros activos. Opcional: ?year=YYYY
    """
    return crud.get_books(session, year)


# ---------------------------------------------------
# Obtener libros disponibles (debe ir antes de /{book_id})
# ---------------------------------------------------
@router.get("/available", response_model=List[BookRead])
def get_available_books(session: Session = Depends(get_session)):
    """
    Retorna todos los libros activos que tienen al menos una copia disponible.
    """
    books = crud.get_available_books(session)
    if not books:
        raise HTTPException(status_code=404, detail="No hay libros disponibles actualmente.")

    return [
        BookRead(
            id=b.id,
            title=b.title,
            isbn=b.isbn,
            year_publication=b.year_publication,
            copies_available=b.copies_available,
            is_active=b.is_active,
            authors=b.authors
        )
        for b in books
    ]


# ---------------------------------------------------
# Obtener los autores asociados a un libro específico
# ---------------------------------------------------
@router.get("/{book_id}/authors", response_model=List[AuthorRead])
def get_authors_by_book(book_id: int, session: Session = Depends(get_session)):
    """
    Retorna todos los autores activos asociados a un libro específico.
    """
    book = crud.get_book_by_id(session, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Libro no encontrado")

    active_authors = [author for author in book.authors if author.is_active]
    if not active_authors:
        raise HTTPException(status_code=404, detail="El libro no tiene autores activos asociados.")

    return active_authors


# ---------------------------------------------------
# Obtener un libro por ID
# ---------------------------------------------------
@router.get("/{book_id}", response_model=BookRead)
def get_book_endpoint(book_id: int, session: Session = Depends(get_session)):
    """
    Obtener un libro por ID (incluye autores asociados).
    """
    return crud.get_book_by_id(session, book_id)


# ---------------------------------------------------
# Actualizar un libro
# ---------------------------------------------------
@router.put("/{book_id}", response_model=BookRead)
def update_book_endpoint(book_id: int, data: BookCreate, session: Session = Depends(get_session)):
    """
    Actualizar un libro. Se valida ISBN único y copias >= 0.
    """
    payload = data.dict()
    return crud.update_book(session, book_id, payload)


# ---------------------------------------------------
# Eliminar (soft delete) un libro
# ---------------------------------------------------
@router.delete("/{book_id}")
def delete_book_endpoint(book_id: int, session: Session = Depends(get_session)):
    """
    Soft delete de un libro (marca is_active=False).
    """
    return crud.soft_delete_book(session, book_id)
