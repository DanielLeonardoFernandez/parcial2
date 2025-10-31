# 📘 Gestión de Libros y Autores (Parcial 2)

## 🧩 Descripción general

Este proyecto desarrollado con **FastAPI** y **SQLModel**, gestiona información de **libros** y **autores**, manteniendo una relación **muchos a muchos** entre ambas entidades.

Permite registrar, consultar, actualizar y eliminar libros y autores, además de vincular autores a libros específicos mediante endpoints especializados.

## Cómo Clonarlo:

1. Abre pycharm 

2. Dale a la opcion: Clonar repositorio
y metes el link que se encuentra en github en el boton **<>code**: https://github.com/DanielLeonardoFernandez/parcial2.git

3. Crea un terminal y pon este comando:   **pip install -r requirements.txt**

4. Con los requerimientos instalados, ahora activa el localhost con este comando: **uvicorn main:app --reload**   


---

## 🗂️ Modelos y relaciones

### **1. Author**

Representa a un autor dentro del sistema.

| Campo | Tipo de dato | Descripción |
|--------|-----------|-------------|
| `id` | int  | Identificador único del autor |
| `name` | str | Nombre completo del autor |
| `country` | str | País de origen |
| `birth_year` | int | Año de nacimiento |
| `is_active` | bool | Indica si el autor está activo |

🔗 **Relaciones:**
- Un autor puede estar asociado a **múltiples libros** mediante la tabla intermedia `BookAuthorLink`.

---

### **2. Book**

Representa un libro disponible en el sistema.

| Campo | Tipo de dato | Descripción |
|--------|-----------|-------------|
| `id` | int  | Identificador único del libro |
| `title` | str | Título del libro |
| `isbn` | str | Código ISBN |
| `year_publication` | int | Año de publicación |
| `copies_available` | int | Copias disponibles |
| `is_active` | bool | Indica si el libro está activo |

🔗 **Relaciones:**
- Un libro puede tener **uno o varios autores** mediante `BookAuthorLink`.

---

### **3. BookAuthorLink**

Tabla intermedia que implementa la relación **muchos a muchos** entre `Book` y `Author`.

| Campo | Tipo de dato | Descripción |
|--------|-------|-------------|
| `book_id` | int  | ID del libro |
| `author_id` | int  | ID del autor |

---

## 🔗 Relaciones generales del sistema

## ⚙️ Endpoints principales

### 📚 **Books**

| Método | Endpoint | Descripción | Cuerpo esperado |
|--------|-----------|--------------|----------------|
| **GET** | `/books/` | Obtiene todos los libros activos | - |
| **GET** | `/books/{id}` | Obtiene un libro específico | - |
| **POST** | `/books/` | Crea un nuevo libro | `{ "title": "string", "isbn": "string", "year_publication": 0, "copies_available": 0, "authors": [1,2] }` |
| **PUT** | `/books/{id}` | Actualiza los datos de un libro y sus autores | Igual que POST |
| **DELETE** | `/books/{id}` | Desactiva (elimina lógicamente) un libro | - |

---

### ✍️ **Authors**

| Método | Endpoint | Descripción | Cuerpo esperado |
|--------|-----------|--------------|----------------|
| **GET** | `/authors/` | Lista todos los autores activos | - |
| **GET** | `/authors/{id}` | Muestra un autor específico | - |
| **POST** | `/authors/` | Crea un nuevo autor | `{ "name": "string", "country": "string", "birth_year": 0 }` |
| **PUT** | `/authors/{id}` | Actualiza los datos de un autor | Igual que POST |
| **DELETE** | `/authors/{id}` | Desactiva (elimina lógicamente) un autor | - |

---
### 🔗 Associations (Book ↔ Author)

| Método | Endpoint | Descripción | Cuerpo esperado | Respuesta esperada |
|--------|-----------|--------------|----------------|----------------|
| **POST** | `/associations/` | Crea una relación entre un libro y un autor | `?book_id=1&author_id=2` | ✅ **201** → Asociación creada <br> ⚠️ **404** → Libro o autor no encontrado/inactivo <br> ⚠️ **409** → Asociación ya existente |
| **GET** | `/associations/` | Lista todas las asociaciones libro-autor existentes | - | ✅ **200** → Lista de asociaciones <br> ⚠️ **404** → No existen asociaciones registradas |
| **DELETE** | `/associations/` | Elimina una relación entre un libro y un autor | `?book_id=1&author_id=2` | ✅ **200** → Asociación eliminada <br> ⚠️ **404** → Asociación no encontrada |

---

### ⚠️ Manejo de errores HTTP

| Código | Tipo | Descripción | Causa común |
|--------|------|-------------|--------------|
| **200 OK** | Éxito | La solicitud se procesó correctamente. | Operaciones `GET` o `DELETE` exitosas. |
| **201 Created** | Creación | Recurso creado correctamente. | Asociación o registro nuevo insertado. |
| **400 Bad Request** | Error del cliente | Solicitud mal formada o con datos inválidos. | Datos faltantes o tipos de dato incorrectos. |
| **404 Not Found** | No encontrado | El recurso solicitado no existe o está inactivo. | Libro, autor o asociación inexistente. |
| **409 Conflict** | Conflicto | El recurso ya existe o viola una restricción. | Asociación duplicada o conflicto de datos. |


### 🧱 Estructura del proyecto

    
    
        parcial2/
        ├─ crud.py
        ├─ db.py
        ├─ main.py
        ├─ models.py
        ├─ schemas.py
        ├─ requirements.txt
        └─ routes/
           ├─ authors.py
           └─ books.py
