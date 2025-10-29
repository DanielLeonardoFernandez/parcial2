from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from db import get_session
from models import BookAuthorLink, Book, Author

router = APIRouter(prefix="/associations", tags=["Asociaciones"])


# -------------------------
#       Crear asociación
# -------------------------
@router.post("/", status_code=201)
def create_association(book_id: int, author_id: int, session: Session = Depends(get_session)):
    """
    Crea una relación entre un libro y un autor.
    - book_id: ID del libro.
    - author_id: ID del autor.
    """
    # Validar existencia de libro y autor
    book = session.get(Book, book_id)
    author = session.get(Author, author_id)

    if not book or not book.is_active:
        raise HTTPException(status_code=404, detail="Libro no encontrado o inactivo.")
    if not author or not author.is_active:
        raise HTTPException(status_code=404, detail="Autor no encontrado o inactivo.")

    # Verificar si ya existe la asociación
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
    return {"message": f"Asociación creada: Libro {book_id} ↔ Autor {author_id}"}


