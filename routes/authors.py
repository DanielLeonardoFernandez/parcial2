from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List, Optional
from db import get_session
from schemas import AuthorCreate, AuthorRead, BookRead
import crud
from models import Author, Book

router = APIRouter(prefix="/authors", tags=["Authors"])


# ---------------------------------------------------
# Crear un nuevo autor
# ---------------------------------------------------
@router.post("/", response_model=AuthorRead, status_code=201)
def create_author_endpoint(data: AuthorCreate, session: Session = Depends(get_session)):
    """
    Crear un nuevo autor en la base de datos.

    - **name**: nombre del autor
    - **country**: país de origen
    - **birth_year**: año de nacimiento
    """
    author = crud.create_author(session, data)
    return AuthorRead.from_orm(author)


# ---------------------------------------------------
# Listar autores activos (opcional: filtrar por país)
# ---------------------------------------------------
@router.get("/", response_model=List[AuthorRead])
def list_authors(
    country: Optional[str] = Query(None, description="Filtrar autores por país"),
    session: Session = Depends(get_session)
):
    """
    Listar todos los autores activos. Puedes filtrar por país si lo deseas.
    """
    authors = crud.get_authors(session, country)
    return [AuthorRead.from_orm(a) for a in authors]


# Listar autores eliminados
@router.get("/deleted", response_model=List[AuthorRead])
def list_deleted_authors(session: Session = Depends(get_session)):
    authors = session.exec(select(Author).where(Author.is_active == False)).all()
    if not authors:
        raise HTTPException(status_code=404, detail="No hay autores eliminados.")
    return [AuthorRead.from_orm(a) for a in authors]

# Recuperar autor eliminado
@router.patch("/{author_id}/recover", response_model=AuthorRead)
def recover_author(author_id: int, session: Session = Depends(get_session)):
    """
    Recuperar un autor eliminado (marca is_active=True).
    También reactiva libros asociados si estaban inactivos por este autor.
    """
    # Traer autor incluyendo inactivos
    author = crud.get_author_by_id_include_inactive(session, author_id)
    if author.is_active:
        raise HTTPException(status_code=400, detail="El autor ya está activo.")

    # Reactivar el autor
    author.is_active = True

    # Reactivar libros asociados que quedaron inactivos solo por este autor
    for book in author.books:
        if not book.is_active and all(not a.is_active for a in book.authors if a.id != author.id):
            book.is_active = True
            session.add(book)

    session.add(author)
    session.commit()
    session.refresh(author)
    return AuthorRead.from_orm(author)


# ---------------------------------------------------
# Obtener un autor por ID
# ---------------------------------------------------
@router.get("/{author_id}", response_model=AuthorRead)
def get_author(author_id: int, session: Session = Depends(get_session)):
    """
    Obtener un autor específico por su ID. Retorna también sus libros asociados.
    """
    author = crud.get_author_by_id(session, author_id)
    return AuthorRead.from_orm(author)


# ---------------------------------------------------
# Actualizar un autor
# ---------------------------------------------------
@router.put("/{author_id}", response_model=AuthorRead)
def update_author(author_id: int, data: AuthorCreate, session: Session = Depends(get_session)):
    """
    Actualizar la información de un autor existente.
    """
    updated = crud.update_author(session, author_id, data.dict())
    return AuthorRead.from_orm(updated)


# ---------------------------------------------------
# Eliminar (soft delete) un autor
# ---------------------------------------------------
@router.delete("/{author_id}")
def delete_author(author_id: int, session: Session = Depends(get_session)):
    """
    Realizar un *soft delete* del autor (marca is_active=False).
    """
    return crud.soft_delete_author(session, author_id)


# ---------------------------------------------------
# Obtener libros asociados a un autor específico
# ---------------------------------------------------
@router.get("/{author_id}/books", response_model=List[BookRead])
def get_books_by_author(author_id: int, session: Session = Depends(get_session)):
    """
    Retorna todos los libros activos asociados a un autor específico.
    """
    author = crud.get_author_by_id(session, author_id)
    active_books = [b for b in author.books if b.is_active]
    if not active_books:
        raise HTTPException(status_code=404, detail="El autor no tiene libros activos registrados.")
    return [BookRead.from_orm(b) for b in active_books]

