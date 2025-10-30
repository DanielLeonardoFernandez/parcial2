from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List, Optional
from models import Book
from db import get_session
from schemas import BookCreate, BookRead, BookUpdate, AuthorRead
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

# Listar libros eliminados
@router.get("/deleted", response_model=List[BookRead])
def list_deleted_books(session: Session = Depends(get_session)):
    """
    Listar todos los libros que han sido eliminados (is_active=False).
    """
    books = session.exec(select(Book).where(Book.is_active == False)).all()
    if not books:
        raise HTTPException(status_code=404, detail="No hay libros eliminados.")
    return [BookRead.from_orm(b) for b in books]


# Recuperar libro eliminado
@router.patch("/{book_id}/recover", response_model=BookRead)
def recover_book(book_id: int, session: Session = Depends(get_session)):
    """
    Recuperar un libro eliminado (marca is_active=True).
    También reactiva autores asociados si todos estaban eliminados.
    """
    # ✅ Usamos la nueva función que permite traer libros inactivos
    book = crud.get_book_by_id_include_inactive(session, book_id)
    if book.is_active:
        raise HTTPException(status_code=400, detail="El libro ya está activo.")

    # Reactivar el libro
    book.is_active = True

    # Reactivar autores asociados si están inactivos
    for autor in book.authors:
        if not autor.is_active:
            autor.is_active = True

    session.add(book)
    session.commit()
    session.refresh(book)
    return BookRead.from_orm(book)


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
def update_book_endpoint(book_id: int, data: BookUpdate, session: Session = Depends(get_session)):
    """
    Actualiza los datos de un libro (incluidos los autores asociados).
    """
    update_data = data.dict(exclude_unset=True)
    book = crud.update_book(session, book_id, update_data)
    return BookRead.from_orm(book)


# ---------------------------------------------------
# Eliminar (soft delete) un libro
# ---------------------------------------------------
@router.delete("/{book_id}")
def delete_book_endpoint(book_id: int, session: Session = Depends(get_session)):
    """
    Realiza un *soft delete* de un libro (marca is_active=False).
    Valida que las copias disponibles sean coherentes (>= 0).
    """
    book = crud.get_book_by_id(session, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Libro no encontrado.")
    if not book.is_active:
        raise HTTPException(status_code=400, detail="El libro ya está eliminado.")

    # Validar que las copias disponibles no sean negativas
    if book.copies_available < 0:
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar el libro porque las copias disponibles son negativas."
        )

    # Marcar como inactivo (soft delete)
    book.is_active = False

    session.add(book)
    session.commit()
    session.refresh(book)

    return {"message": f"Libro '{book.title}' eliminado correctamente (soft delete)."}



