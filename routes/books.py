from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Optional

from db import get_session
from models import Book, BookCreate, BookRead, AuthorRead  # las clases están en models.py
import crud  # usa las funciones create_book, get_books, get_book_by_id, update_book, soft_delete_book

router = APIRouter(prefix="/books", tags=["Books"])


@router.post("/", response_model=BookRead, status_code=201)
def create_book_endpoint(data: BookCreate, session: Session = Depends(get_session)):
    """
    Crear un nuevo book y asociarlo con autores (author_ids en BookCreate).
    """
    book = Book.from_orm(data)
    return crud.create_book(session, book, data.author_ids or [])


@router.get("/", response_model=List[BookRead])
def list_books_endpoint(
    year: Optional[int] = Query(None, description="Filtrar por año de publicación"),
    session: Session = Depends(get_session)
):
    """
    Listar todos los books activos. Opcional: ?year=YYYY
    """
    return crud.get_books(session, year)


@router.get("/{book_id}", response_model=BookRead)
def get_book_endpoint(book_id: int, session: Session = Depends(get_session)):
    """
    Obtener un book por id (incluye autores asociados).
    """
    return crud.get_book_by_id(session, book_id)


@router.put("/{book_id}", response_model=BookRead)
def update_book_endpoint(book_id: int, data: BookCreate, session: Session = Depends(get_session)):
    """
    Actualizar un book. Se usa data.dict() y la validación de CRUD (ISBN único, copias >= 0).
    Nota: BookCreate se reutiliza aquí; si quieres campos opcionales para PATCH, podemos crear BookUpdate.
    """
    # En crud.update_book se usa exclude_unset-like behavior si le pasas solo los campos que quieras cambiar.
    payload = data.dict()
    return crud.update_book(session, book_id, payload)


@router.delete("/{book_id}")
def delete_book_endpoint(book_id: int, session: Session = Depends(get_session)):
    """
    Soft delete de un book (marca is_active=False).
    """
    return crud.soft_delete_book(session, book_id)

# ---------------------------------------------------
# Obtener los autores asociados a un libro específico
# ---------------------------------------------------
@router.get("/{book_id}/authors", response_model=list[AuthorRead])
def get_authors_by_book(book_id: int, session: Session = Depends(get_session)):
    """
    Retorna todos los autores activos asociados a un libro específico.
    """
    book = crud.get_book_by_id(session, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Libro no encontrado")

    # Filtrar solo autores activos
    active_authors = [author for author in book.authors if author.is_active]
    if not active_authors:
        raise HTTPException(status_code=404, detail="El libro no tiene autores activos asociados.")

    return active_authors