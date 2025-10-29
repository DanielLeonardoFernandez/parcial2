from sqlmodel import Session, select
from fastapi import HTTPException, status
from models import Author, Book


# -------------------------
#       CRUD AUTORES
# -------------------------

def create_author(session: Session, data: Author):
    # Validar duplicado por nombre y país (opcional)
    existing = session.exec(
        select(Author).where(Author.name == data.name, Author.country == data.country)
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="El autor ya existe en la base de datos.")

    session.add(data)
    session.commit()
    session.refresh(data)
    return data


def get_authors(session: Session, country: str | None = None):
    query = select(Author).where(Author.is_active == True)
    if country:
        query = query.where(Author.country == country)
    return session.exec(query).all()


def get_author_by_id(session: Session, author_id: int):
    author = session.get(Author, author_id)
    if not author or not author.is_active:
        raise HTTPException(status_code=404, detail="Autor no encontrado o inactivo.")
    session.refresh(author)
    return author


def update_author(session: Session, author_id: int, data: dict):
    author = session.get(Author, author_id)
    if not author or not author.is_active:
        raise HTTPException(status_code=404, detail="Autor no encontrado o inactivo.")

    for key, value in data.items():
        setattr(author, key, value)

    session.add(author)
    session.commit()
    session.refresh(author)
    return author


def soft_delete_author(session: Session, author_id: int):
    author = session.get(Author, author_id)
    if not author or not author.is_active:
        raise HTTPException(status_code=404, detail="Autor no encontrado o ya eliminado.")

    author.is_active = False

    # Regla de negocio: si un autor es eliminado, los libros se mantienen.
    # (Se podría agregar que si todos los autores de un libro están inactivos, marcar ese libro inactivo)

    session.add(author)
    session.commit()
    return {"message": f"Autor {author.name} marcado como inactivo."}

# -------------------------
#        CRUD LIBROS
# -------------------------

def create_book(session: Session, data: Book, author_ids: list[int]):
    # Validar ISBN único
    existing = session.exec(select(Book).where(Book.isbn == data.isbn)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe un libro con ese ISBN.")

    # Validar copias
    if data.copies_available < 0:
        raise HTTPException(status_code=400, detail="El número de copias no puede ser negativo.")

    # Asociar autores si se proporcionan
    if author_ids:
        authors = session.exec(select(Author).where(Author.id.in_(author_ids), Author.is_active == True)).all()
        if not authors:
            raise HTTPException(status_code=404, detail="No se encontraron autores válidos.")
        data.authors = authors

    session.add(data)
    session.commit()
    session.refresh(data)
    return data


def get_books(session: Session, year: int | None = None):
    query = select(Book).where(Book.is_active == True)
    if year:
        query = query.where(Book.year_publication == year)
    return session.exec(query).all()


def get_book_by_id(session: Session, book_id: int):
    book = session.get(Book, book_id)
    if not book or not book.is_active:
        raise HTTPException(status_code=404, detail="Libro no encontrado o inactivo.")
    session.refresh(book)
    return book


def update_book(session: Session, book_id: int, data: dict):
    book = session.get(Book, book_id)
    if not book or not book.is_active:
        raise HTTPException(status_code=404, detail="Book not found")

    # Evitar que se intente asignar author_ids directamente
    data.pop("author_ids", None)

    # Validar ISBN si se cambia
    if "isbn" in data and data["isbn"] != book.isbn:
        existing = session.exec(select(Book).where(Book.isbn == data["isbn"])).first()
        if existing:
            raise HTTPException(status_code=409, detail="ISBN already exists")

    # Validar copias disponibles
    if "copies_available" in data and data["copies_available"] < 0:
        raise HTTPException(status_code=400, detail="Copies cannot be negative")

    for key, value in data.items():
        setattr(book, key, value)

    try:
        session.add(book)
        session.commit()
        session.refresh(book)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating book: {str(e)}")

    return book


def soft_delete_book(session: Session, book_id: int):
    book = session.get(Book, book_id)
    if not book or not book.is_active:
        raise HTTPException(status_code=404, detail="Libro no encontrado o ya eliminado.")

    # Validación de copias
    if book.copies_available < 0:
        raise HTTPException(status_code=400, detail="El libro tiene un número inválido de copias.")

    book.is_active = False
    session.add(book)
    session.commit()
    return {"message": f"Libro '{book.title}' marcado como inactivo."}
