from sqlmodel import Session, select
from fastapi import HTTPException, status
from models import Author, Book
from schemas import AuthorCreate, AuthorRead, BookRead, BookCreate

# -------------------------
#       CRUD AUTORES
# -------------------------


def create_author(session: Session, data: AuthorCreate):
    author = Author.from_orm(data)  # Convierte Pydantic -> SQLModel
    session.add(author)
    session.commit()
    session.refresh(author)
    return author



def get_authors(session: Session, country: str | None = None):
    query = select(Author).where(Author.is_active == True)
    if country:
        query = query.where(Author.country == country)
    authors = session.exec(query).all()
    if not authors:
        raise HTTPException(status_code=404, detail="No se encontraron autores activos.")
    return authors


def get_author_by_id(session: Session, author_id: int):
    author = session.get(Author, author_id)
    if not author or not author.is_active:
        raise HTTPException(status_code=404, detail="Autor no encontrado o inactivo.")
    session.refresh(author)
    return author

def get_author_by_id_include_inactive(session: Session, author_id: int):
    author = session.get(Author, author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Autor no encontrado.")
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

    # Soft delete del autor
    author.is_active = False
    session.add(author)

    # Revisar libros asociados
    for book in author.books:
        # Verificar si todos los autores del libro están inactivos
        if all(a.is_active == False for a in book.authors):
            book.is_active = False
            session.add(book)

    session.commit()
    return {"message": f"Autor {author.name} marcado como inactivo y libros afectados revisados."}


# -------------------------
#        CRUD LIBROS
# -------------------------

def create_book(session: Session, data: BookCreate, author_ids: list[int]):
    # Validar ISBN único
    existing = session.exec(select(Book).where(Book.isbn == data.isbn)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe un libro con ese ISBN.")

    # Validar copias
    if data.copies_available < 0:
        raise HTTPException(status_code=400, detail="El número de copias no puede ser negativo.")

    # Crear instancia SQLModel del libro
    book = Book(
        title=data.title,
        isbn=data.isbn,
        year_publication=data.year_publication,
        copies_available=data.copies_available
    )

    # Asociar autores si se proporcionan
    if author_ids:
        authors = session.exec(
            select(Author).where(Author.id.in_(author_ids), Author.is_active == True)
        ).all()
        if not authors:
            raise HTTPException(status_code=404, detail="No se encontraron autores válidos.")
        book.authors = authors

    session.add(book)
    session.commit()
    session.refresh(book)
    return book


def get_books(session: Session, year: int | None = None):
    query = select(Book).where(Book.is_active == True)
    if year:
        query = query.where(Book.year_publication == year)
    books = session.exec(query).all()
    if not books:
        raise HTTPException(status_code=404, detail="No se encontraron libros activos.")
    return books


def get_book_by_id(session: Session, book_id: int):
    book = session.get(Book, book_id)
    if not book or not book.is_active:
        raise HTTPException(status_code=404, detail="Libro no encontrado o inactivo.")
    session.refresh(book)
    return book

# En crud.py
def get_book_by_id_include_inactive(session: Session, book_id: int):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Libro no encontrado.")
    session.refresh(book)
    return book


def update_book(session: Session, book_id: int, data: dict):
    book = session.get(Book, book_id)
    if not book or not book.is_active:
        raise HTTPException(status_code=404, detail="Book not found")

    # 🚨 Validar si no se envió ningún dato para actualizar
    if not data:
        raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar el libro.")

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

def get_available_books(session: Session):
    """
    Devuelve todos los libros activos con al menos una copia disponible.
    """
    query = select(Book).where(Book.is_active == True, Book.copies_available > 0)
    return session.exec(query).all()
