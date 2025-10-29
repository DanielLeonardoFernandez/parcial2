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

# Listar asociaciones eliminadas (libros o autores inactivos)
@router.get("/deleted")
def list_deleted_associations(session: Session = Depends(get_session)):
    associations = session.exec(select(BookAuthorLink)).all()
    deleted_links = [
        link for link in associations
        if not session.get(Book, link.book_id).is_active or not session.get(Author, link.author_id).is_active
    ]
    if not deleted_links:
        raise HTTPException(status_code=404, detail="No hay asociaciones eliminadas.")
    return deleted_links

# Recuperar asociación eliminada (solo reactiva si ambos están activos)
@router.patch("/recover")
def recover_association(book_id: int, author_id: int, session: Session = Depends(get_session)):
    link = session.exec(
        select(BookAuthorLink).where(
            BookAuthorLink.book_id == book_id,
            BookAuthorLink.author_id == author_id
        )
    ).first()
    if not link:
        raise HTTPException(status_code=404, detail="Asociación no encontrada.")

    book = session.get(Book, book_id)
    author = session.get(Author, author_id)
    if not book or not author:
        raise HTTPException(status_code=400, detail="No se puede recuperar la asociación, libro o autor no existen.")
    if not book.is_active or not author.is_active:
        raise HTTPException(status_code=400, detail="No se puede recuperar la asociación, libro o autor no están activos.")

    return {"message": f"Asociación activa: Libro {book_id} ↔ Autor {author_id}"}
