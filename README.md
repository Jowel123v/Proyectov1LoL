# 🎮 Proyecto LoL Worlds API

**Autor:** Joel Marín  
**Universidad:** Universidad Católica de Colombia  
**Programa:** Ingeniería de Sistemas  
**Versión:** 1.0.0  
**Framework:** FastAPI + SQLModel  
**Base de datos:** SQLite  

---

## 🧩 Descripción general

El proyecto **LoL Worlds API** es una aplicación backend construida con **FastAPI** que gestiona y analiza información del **Campeonato Mundial de League of Legends (LoL Worlds)**.  

El sistema permite registrar, consultar, filtrar y eliminar de forma lógica datos sobre:

- 🧠 **Campeones (Champion)**
- 🛡️ **Equipos (Team)**
- ⚔️ **Partidas (MatchSummary)**

El propósito principal es servir como base para una guía analítica que brinde estadísticas y tendencias competitivas sobre el juego, aplicando buenas prácticas de desarrollo, persistencia de datos y control de registros mediante **eliminación lógica (soft delete)**.

---

## 🎯 Objetivos del proyecto

**Objetivo general**  
Desarrollar una API REST que gestione información relacionada con campeones, equipos y partidas del Mundial de League of Legends, integrando relaciones entre modelos y operaciones CRUD completas con control lógico de los registros.

**Objetivos específicos**
- Implementar modelos relacionales con **1:N** y **N:M** usando SQLModel.  
- Crear endpoints CRUD con **manejo de excepciones** y **soft delete**.  
- Permitir **búsquedas** y **filtrados** por atributos específicos.  
- Agregar **historial y restauración** de registros eliminados.  
- Establecer la base para **reportes exportables (CSV, XLSX, PDF)**.  

---

## ⚙️ Tecnologías utilizadas

| Tecnología | Descripción |
|-------------|--------------|
| **FastAPI** | Framework principal del backend |
| **SQLModel** | ORM que combina Pydantic y SQLAlchemy |
| **SQLite** | Base de datos ligera y local |
| **Uvicorn** | Servidor ASGI para ejecutar la API |
| **Pydantic** | Validación de datos |
| **Python 3.11+** | Lenguaje de programación principal |

---

## 🧱 Estructura del proyecto

