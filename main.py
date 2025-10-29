from fastapi import FastAPI
from db import create_db_and_tables
from routers import authors, books  # creados luego

app = FastAPI(title="Parcial2 - Biblioteca")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# incluiremos routers cuando estén listos
# app.include_router(authors.router)
# app.include_router(books.router)
