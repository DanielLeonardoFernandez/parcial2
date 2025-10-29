from fastapi import FastAPI
from db import create_db_and_tables
from routes import authors, books, associations

app = FastAPI(title="Parcial2 - Sistema de Biblioteca")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

app.include_router(authors.router)
app.include_router(books.router)
app.include_router(associations.router)