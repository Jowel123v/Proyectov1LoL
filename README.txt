

```markdown
#  Proyecto LoL Worlds API

**Autor:** Joel Marín
**Universidad:** Universidad Católica de Colombia
**Programa:** Ingeniería de Sistemas
**Versión:** 1.0.0
**Framework:** FastAPI + SQLModel
**Base de datos:** SQLite

---

##  Descripción general

El proyecto **LoL Worlds API** es una aplicación backend construida con **FastAPI** que gestiona y analiza información del **Campeonato Mundial de League of Legends (LoL Worlds)**.

El sistema permite registrar, consultar, filtrar y eliminar de forma lógica datos sobre:

- **Campeones** (Champion)
- **Equipos** (Team)
- **Partidas** (MatchSummary)

El propósito principal es servir como base para una guía analítica que brinde estadísticas y tendencias competitivas sobre el juego, aplicando buenas prácticas de desarrollo, persistencia de datos y control de registros mediante **eliminación lógica (soft delete)**.

---

##  Objetivos del proyecto

### Objetivo general
Desarrollar una API REST que gestione información relacionada con campeones, equipos y partidas del Mundial de League of Legends, integrando relaciones entre modelos y operaciones CRUD completas con control lógico de los registros.

### Objetivos específicos
- Implementar modelos relacionales con **1:N** y **N:M** usando SQLModel.
- Crear endpoints CRUD con **manejo de excepciones** y **soft delete**.
- Permitir **búsquedas** y **filtrados** por atributos específicos.
- Agregar **historial y restauración** de registros eliminados.
- Establecer la base para reportes exportables (CSV, XLSX, PDF).

---

##  Tecnologías utilizadas

| Tecnología | Descripción |
|-------------|--------------|
| **FastAPI** | Framework principal del backend |
| **SQLModel** | ORM que combina Pydantic y SQLAlchemy |
| **SQLite** | Base de datos ligera y local |
| **Uvicorn** | Servidor ASGI para ejecutar la API |
| **Pydantic** | Validación de datos |
| **Python 3.11+** | Lenguaje de programación principal |

---

##  Estructura del proyecto

```

ProyectoLoL/
├── main.py                     # Archivo principal con las rutas y configuración
├── data/
│   └── models.py               # Modelos y relaciones ORM
├── operations/
│   └── operations_db.py        # CRUD, filtros, búsquedas y eliminación lógica
├── database_lol.db             # Base de datos local SQLite
├── requirements.txt            # Dependencias del entorno virtual
└── README.md                   # Documentación del proyecto

````

---

##  Modelos de datos y relaciones

###  Champion
| Atributo | Tipo | Descripción |
|-----------|------|-------------|
| `id` | int | Autoincremental (clave primaria, inmutable por el usuario) |
| `slug` | str | Alias único del campeón |
| `name` | str | Nombre del campeón |
| `pick_rate` | float | Frecuencia de selección |
| `ban_rate` | float | Frecuencia de bloqueo |
| `win_rate` | float | Porcentaje de victorias |
| `kda` | float | Promedio de kills/deaths/assists |
| `is_deleted` | bool | Campo interno para eliminación lógica |

---

###  Team
| Atributo | Tipo | Descripción |
|-----------|------|-------------|
| `id` | int | Autoincremental |
| `name` | str | Nombre del equipo |
| `region` | str | Región (LCK, LPL, LEC, LCS) |
| `wins` | int | Número de victorias |
| `losses` | int | Número de derrotas |
| `avg_kda` | float | Promedio de KDA del equipo |
| `favorite_champions` | str | Campeones más usados (CSV) |
| `is_deleted` | bool | Campo interno (soft delete) |

**Relaciones:**
- 1:N con `MatchSummary` como `team_a`, `team_b` y `winner`.

---

###  MatchSummary
| Atributo | Tipo | Descripción |
|-----------|------|-------------|
| `id` | int | Autoincremental |
| `stage` | str | Etapa o torneo (Playoffs, Worlds 2025) |
| `team_a_id` | int | Equipo A (FK a Team) |
| `team_b_id` | int | Equipo B (FK a Team) |
| `winner_id` | int | Equipo ganador (FK a Team) |
| `avg_duration_min` | float | Duración promedio |
| `avg_kills_per_game` | float | Kills promedio por partida |
| `is_deleted` | bool | Eliminación lógica |

**Relaciones:**
- `Team` (1:N)
- `Champion` (N:M mediante `MatchChampionLink`)

---

##  Relaciones entre modelos

```mermaid
erDiagram
    CHAMPION {
        int id
        string name
        float win_rate
    }
    TEAM {
        int id
        string name
        string region
    }
    MATCHSUMMARY {
        int id
        string stage
    }
    MATCHCHAMPIONLINK {
        int match_id
        int champion_id
    }

    TEAM ||--o{ MATCHSUMMARY : "participa en"
    TEAM ||--o{ MATCHSUMMARY : "gana"
    MATCHSUMMARY ||--o{ MATCHCHAMPIONLINK : "incluye"
    CHAMPION ||--o{ MATCHCHAMPIONLINK : "aparece en"
````

---

##  Mapa de Endpoints

### **Champions**

| Método   | Ruta                                     | Descripción                 |
| -------- | ---------------------------------------- | --------------------------- |
| `POST`   | `/champions/`                            | Crear un nuevo campeón      |
| `GET`    | `/champions/`                            | Listar campeones activos    |
| `GET`    | `/champions/{id}`                        | Obtener un campeón por ID   |
| `GET`    | `/champions/deleted`                     | Listar campeones eliminados |
| `POST`   | `/champions/{id}/restore`                | Restaurar campeón eliminado |
| `GET`    | `/champions/search?nombre=`              | Buscar por nombre           |
| `GET`    | `/champions/filter/winrate?min_winrate=` | Filtrar por win rate        |
| `PUT`    | `/champions/{id}`                        | Actualizar información      |
| `DELETE` | `/champions/{id}`                        | Eliminación lógica          |

---

### **Teams**

| Método   | Ruta                     | Descripción                |
| -------- | ------------------------ | -------------------------- |
| `POST`   | `/teams/`                | Crear un nuevo equipo      |
| `GET`    | `/teams/`                | Listar equipos activos     |
| `GET`    | `/teams/deleted`         | Listar equipos eliminados  |
| `POST`   | `/teams/{id}/restore`    | Restaurar equipo eliminado |
| `GET`    | `/teams/search?nombre=`  | Buscar equipo por nombre   |
| `GET`    | `/teams/region/{region}` | Filtrar equipos por región |
| `PUT`    | `/teams/{id}`            | Actualizar equipo          |
| `DELETE` | `/teams/{id}`            | Eliminar lógicamente       |

---

### **Matches**

| Método   | Ruta                        | Descripción                 |
| -------- | --------------------------- | --------------------------- |
| `POST`   | `/matches/`                 | Crear una partida           |
| `GET`    | `/matches/`                 | Listar partidas activas     |
| `GET`    | `/matches/deleted`          | Listar partidas eliminadas  |
| `POST`   | `/matches/{id}/restore`     | Restaurar partida eliminada |
| `GET`    | `/matches/search?etapa=`    | Buscar por etapa o torneo   |
| `GET`    | `/matches/winner/{team_id}` | Filtrar por equipo ganador  |
| `DELETE` | `/matches/{id}`             | Eliminar lógicamente        |

---

##  Reglas de negocio

* **Soft delete:** no se eliminan registros de la base de datos, se marcan con `is_deleted=True`.
* **Historial:** visible mediante rutas `/deleted`.
* **Restauración:** recuperación controlada de datos eliminados.
* **Manejo de excepciones:**

  * 404 → registro no encontrado o eliminado.
  * 400 → estado inválido (ya eliminado/restaurado).
  * 500 → error de base de datos con rollback.
* **ID inmutable:** el usuario no puede asignar ni modificar IDs manualmente.
* **Consultas limpias:** todas las búsquedas y listados excluyen eliminados por defecto.

---

## ⚡ Ejecución local

1. **Clonar el repositorio:**

   ```bash
   git clone https://github.com/joelmarin/ProyectoLoL.git
   cd ProyectoLoL
   ```

2. **Crear el entorno virtual:**

   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # En Windows
   ```

3. **Instalar dependencias:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar el servidor:**

   ```bash
   uvicorn main:app --reload
   ```

5. **Abrir la documentación interactiva:**
    [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

##  Próximas mejoras

* Implementar módulo de **reportes en CSV, XLSX o PDF**.
* Añadir **autenticación** y control de roles.
* Endpoint para asociar campeones a partidas (relación N:M).
* Crear un **frontend visual** con gráficos estadísticos.

---



