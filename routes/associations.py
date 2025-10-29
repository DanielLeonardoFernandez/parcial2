from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from db import get_session
from models import BookAuthorLink, Book, Author

router = APIRouter(prefix="/associations", tags=["Asociaciones"])


# ---------------------------------------------------
# Crear una asociación libro-autor
# ---------------------------------------------------
@router.post("/", status_code=201)
def create_association(book_id: int, author_id: int, session: Session = Depends(get_session)):
    """
    Crea una relación entre un libro y un autor.

    - **book_id**: ID del libro
    - **author_id**: ID del autor
    """
    book = session.get(Book, book_id)
    author = session.get(Author, author_id)

    if not book or not book.is_active:
        raise HTTPException(status_code=404, detail="Libro no encontrado o inactivo.")
    if not author or not author.is_active:
        raise HTTPException(status_code=404, detail="Autor no encontrado o inactivo.")

    existing = session.exec(
        select(BookAuthorLink).where(
            BookAuthorLink.book_id == book_id,
            BookAuthorLink.author_id == author_id
        )
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="La asociación ya existe.")

    link = BookAuthorLink(book_id=book_id, author_id=author_id)
    session.add(link)
    session.commit()
    session.refresh(link)

    return {"message": f"Asociación creada: Libro {book_id} ↔ Autor {author_id}"}


# ---------------------------------------------------
# Listar todas las asociaciones
# ---------------------------------------------------
@router.get("/")
def list_associations(session: Session = Depends(get_session)):
    """
    Lista todas las asociaciones libro-autor existentes.
    """
    associations = session.exec(select(BookAuthorLink)).all()
    if not associations:
        raise HTTPException(status_code=404, detail="No existen asociaciones registradas.")
    return associations


# ---------------------------------------------------
# Eliminar una asociación libro-autor
# ---------------------------------------------------
@router.delete("/", status_code=200)
def delete_association(book_id: int, author_id: int, session: Session = Depends(get_session)):
    """
    Elimina la relación entre un libro y un autor.

    - **book_id**: ID del libro
    - **author_id**: ID del autor
    """
    link = session.exec(
        select(BookAuthorLink).where(
            BookAuthorLink.book_id == book_id,
            BookAuthorLink.author_id == author_id
        )
    ).first()
    if not link:
        raise HTTPException(status_code=404, detail="Asociación no encontrada.")

    session.delete(link)
    session.commit()
    return {"message": f"Asociación eliminada: Libro {book_id} ↔ Autor {author_id}"}
