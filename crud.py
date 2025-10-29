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
