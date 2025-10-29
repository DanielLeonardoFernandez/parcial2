from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Optional

from db import get_session
from schemas import BookCreate, BookRead, AuthorRead
import crud

router = APIRouter(prefix="/books", tags=["Books"])


# ---------------------------------------------------
# Crear un nuevo libro
# ---------------------------------------------------
@router.post("/", response_model=BookRead, status_code=201)
def create_book_endpoint(data: BookCreate, session: Session = Depends(get_session)):
    """
    Crear un nuevo libro y asociarlo con autores (author_ids en BookCreate).

    - **title**: título del libro
    - **isbn**: ISBN válido (10 o 13 dígitos, se permiten guiones)
    - **year_publication**: año de publicación
    - **copies_available**: número de copias disponibles (>=0)
    - **author_ids**: lista de IDs de autores asociados
    """
    book = crud.create_book(session, data, data.author_ids or [])
    return BookRead.from_orm(book)


# ---------------------------------------------------
# Listar libros activos (opcional: filtrar por año)
# ---------------------------------------------------
@router.get("/", response_model=List[BookRead])
def list_books_endpoint(
    year: Optional[int] = Query(None, description="Filtrar por año de publicación"),
    session: Session = Depends(get_session)
):
    """
    Listar todos los libros activos. Opcionalmente filtrar por año de publicación.
    """
    books = crud.get_books(session, year)
    return [BookRead.from_orm(b) for b in books]


# ---------------------------------------------------
# Obtener libros disponibles
# ---------------------------------------------------
@router.get("/available", response_model=List[BookRead])
def get_available_books(session: Session = Depends(get_session)):
    """
    Retorna todos los libros activos que tienen al menos una copia disponible.
    """
    books = crud.get_available_books(session)
    if not books:
        raise HTTPException(status_code=404, detail="No hay libros disponibles actualmente.")
    return [BookRead.from_orm(b) for b in books]


# ---------------------------------------------------
# Obtener los autores asociados a un libro específico
# ---------------------------------------------------
@router.get("/{book_id}/authors", response_model=List[AuthorRead])
def get_authors_by_book(book_id: int, session: Session = Depends(get_session)):
    """
    Retorna todos los autores activos asociados a un libro específico.
    """
    book = crud.get_book_by_id(session, book_id)
    active_authors = [a for a in book.authors if a.is_active]
    if not active_authors:
        raise HTTPException(status_code=404, detail="El libro no tiene autores activos asociados.")
    return [AuthorRead.from_orm(a) for a in active_authors]


# ---------------------------------------------------
# Obtener un libro por ID
# ---------------------------------------------------
@router.get("/{book_id}", response_model=BookRead)
def get_book_endpoint(book_id: int, session: Session = Depends(get_session)):
    """
    Obtener un libro por ID (incluye autores asociados).
    """
    book = crud.get_book_by_id(session, book_id)
    return BookRead.from_orm(book)


# ---------------------------------------------------
# Actualizar un libro
# ---------------------------------------------------
@router.put("/{book_id}", response_model=BookRead)
def update_book_endpoint(book_id: int, data: BookCreate, session: Session = Depends(get_session)):
    """
    Actualizar un libro existente.

    - Valida ISBN único
    - Copias >= 0
    - No permite modificar directamente author_ids aquí
    """
    updated = crud.update_book(session, book_id, data.dict(exclude={"author_ids"}))
    return BookRead.from_orm(updated)


# ---------------------------------------------------
# Eliminar (soft delete) un libro
# ---------------------------------------------------
@router.delete("/{book_id}")
def delete_book_endpoint(book_id: int, session: Session = Depends(get_session)):
    """
    Realizar un *soft delete* de un libro (marca is_active=False).
    """
    return crud.soft_delete_book(session, book_id)


# Listar libros eliminados
@router.get("/deleted", response_model=List[BookRead])
def list_deleted_books(session: Session = Depends(get_session)):
    books = session.exec(select(Book).where(Book.is_active == False)).all()
    if not books:
        raise HTTPException(status_code=404, detail="No hay libros eliminados.")
    return [BookRead.from_orm(b) for b in books]


# Recuperar libro eliminado
@router.patch("/{book_id}/recover", response_model=BookRead)
def recover_book(book_id: int, session: Session = Depends(get_session)):
    book = crud.get_book_by_id(session, book_id)
    if not book or book.is_active:
        raise HTTPException(status_code=404, detail="Libro no encontrado o ya activo.")

    book.is_active = True
    session.add(book)
    session.commit()
    session.refresh(book)
    return BookRead.from_orm(book)
