from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Optional
from db import get_session
from models import Author, AuthorCreate, AuthorRead
import crud
from models import BookRead

router = APIRouter(prefix="/authors", tags=["Authors"])

@router.post("/", response_model=AuthorRead, status_code=201)
def create_author(data: AuthorCreate, session: Session = Depends(get_session)):
    """
    Crear un nuevo autor en la base de datos.
    - **name**: nombre del autor
    - **country**: país de origen
    - **birth_year**: año de nacimiento
    """
    author = Author.from_orm(data)
    return crud.create_author(session, author)


@router.get("/", response_model=List[AuthorRead])
def list_authors(
    country: Optional[str] = Query(None, description="Filtrar autores por país"),
    session: Session = Depends(get_session)
):
    """
    Listar todos los autores activos.
    Puedes filtrar por **country** si lo deseas.
    """
    return crud.get_authors(session, country)


@router.get("/{author_id}", response_model=AuthorRead)
def get_author(author_id: int, session: Session = Depends(get_session)):
    """
    Obtener un autor específico por su ID.
    Retorna también sus libros (si los tiene).
    """
    author = crud.get_author_by_id(session, author_id)
    return author


@router.put("/{author_id}", response_model=AuthorRead)
def update_author(author_id: int, data: AuthorCreate, session: Session = Depends(get_session)):
    """
    Actualizar la información de un autor existente.
    """
    return crud.update_author(session, author_id, data.dict())


@router.delete("/{author_id}")
def delete_author(author_id: int, session: Session = Depends(get_session)):
    """
    Realizar un *soft delete* del autor (is_active=False).
    """
    return crud.soft_delete_author(session, author_id)

# ---------------------------------------------------
# Obtener los libros asociados a un autor específico
# ---------------------------------------------------
@router.get("/{author_id}/books", response_model=list[BookRead])
def get_books_by_author(author_id: int, session: Session = Depends(get_session)):
    """
    Retorna todos los libros activos asociados a un autor específico.
    """
    author = crud.get_author_by_id(session, author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Autor no encontrado")

    # Filtrar solo libros activos
    active_books = [book for book in author.books if book.is_active]
    if not active_books:
        raise HTTPException(status_code=404, detail="El autor no tiene libros activos registrados.")

    return active_books