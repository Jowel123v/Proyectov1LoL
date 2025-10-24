from typing import List
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlmodel import SQLModel, Session, create_engine

# Modelos
from data.models import Champion, Team, MatchSummary

# Operaciones (con soft delete, historial, restaurar, búsquedas y filtros)
from operations.operations_db import (
    # Champions
    crear_campeon, listar_campeones, listar_campeones_eliminados, restaurar_campeon,
    buscar_campeon_por_nombre, filtrar_campeones_por_winrate,
    obtener_campeon, actualizar_campeon, eliminar_campeon,

    # Teams
    crear_equipo, listar_equipos, listar_equipos_eliminados, restaurar_equipo,
    buscar_equipo_por_nombre, filtrar_equipo_por_region,
    obtener_equipo, actualizar_equipo, eliminar_equipo,

    # Matches
    crear_resumen, listar_resumenes, listar_resumenes_eliminados, restaurar_resumen,
    buscar_resumen_por_etapa, filtrar_resumen_por_ganador,
)


# CONFIGURACIÓN BASE DE DATOS

DATABASE_URL = "sqlite:///database_lol.db"
engine = create_engine(DATABASE_URL, echo=False)

def crear_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session


# CONFIGURACIÓN FASTAPI

app = FastAPI(
    title="LoL Worlds API",
    description="API para gestión y análisis de campeones, equipos y partidas del Mundial de League of Legends",
    version="1.1.1",
)

@app.on_event("startup")
def on_startup():
    crear_db()


# ROOT / HEALTH

@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Bienvenido a la API de League of Legends Worlds",
        "docs": "/docs",
        "endpoints": [
            "/champions",
            "/teams",
            "/matches",
        ],
    }

@app.get("/health", tags=["Root"])
def health():
    return {"status": "ok"}


# CHAMPIONS  (orden: estáticas -> dinámicas)

@app.post("/champions/", response_model=Champion, tags=["Champions"])
def crear_nuevo_campeon(obj: Champion, session: Session = Depends(get_session)):
    # respuesta de creación NO incluye 'id' ni 'is_deleted' (se controla en operations)
    return crear_campeon(session, obj)

@app.get("/champions/", response_model=List[Champion], tags=["Champions"])
def listar_todos_los_campeones(
    skip: int = 0,
    limit: int = Query(10, le=100),
    include_deleted: bool = Query(False, description="Incluir eliminados lógicamente"),
    session: Session = Depends(get_session)
):
    return listar_campeones(session, skip=skip, limit=limit, include_deleted=include_deleted)

# --- RUTAS ESTÁTICAS
@app.get("/champions/deleted", response_model=List[Champion], tags=["Champions"])
def listar_campeones_borrados(session: Session = Depends(get_session)):
    return listar_campeones_eliminados(session)

@app.post("/champions/{champion_id}/restore", tags=["Champions"])
def restaurar_campeon_por_id(champion_id: int, session: Session = Depends(get_session)):
    if restaurar_campeon(session, champion_id):
        return {"message": "Campeón restaurado correctamente"}
    raise HTTPException(status_code=404, detail="No fue posible restaurar el campeón")

@app.get("/champions/search/", response_model=List[Champion], tags=["Champions"])
def buscar_campeon(nombre: str = Query(..., min_length=1), session: Session = Depends(get_session)):
    return buscar_campeon_por_nombre(session, nombre)

@app.get("/champions/filter/winrate/", response_model=List[Champion], tags=["Champions"])
def filtrar_campeones_por_winrate_minimo(min_winrate: float = Query(0.5, ge=0.0), session: Session = Depends(get_session)):
    return filtrar_campeones_por_winrate(session, min_winrate)

# --- RUTAS CON PARÁMETRO
@app.get("/champions/{champion_id}", response_model=Champion, tags=["Champions"])
def obtener_campeon_por_id(champion_id: int, session: Session = Depends(get_session)):
    return obtener_campeon(session, champion_id)

@app.put("/champions/{champion_id}", response_model=Champion, tags=["Champions"])
def actualizar_datos_campeon(champion_id: int, obj: Champion, session: Session = Depends(get_session)):
    return actualizar_campeon(session, champion_id, obj)

@app.delete("/champions/{champion_id}", tags=["Champions"])
def eliminar_campeon_por_id(champion_id: int, session: Session = Depends(get_session)):
    if eliminar_campeon(session, champion_id):
        return {"message": "Campeón eliminado correctamente"}
    raise HTTPException(status_code=404, detail="Campeón no encontrado")


# TEAMS  (orden: estáticas -> dinámicas)

@app.post("/teams/", response_model=Team, tags=["Teams"])
def crear_nuevo_equipo(obj: Team, session: Session = Depends(get_session)):
    return crear_equipo(session, obj)

@app.get("/teams/", response_model=List[Team], tags=["Teams"])
def listar_todos_los_equipos(
    skip: int = 0,
    limit: int = Query(10, le=100),
    include_deleted: bool = Query(False, description="Incluir eliminados lógicamente"),
    session: Session = Depends(get_session)
):
    return listar_equipos(session, skip=skip, limit=limit, include_deleted=include_deleted)

# --- RUTAS ESTÁTICAS (antes de /{team_id})
@app.get("/teams/deleted", response_model=List[Team], tags=["Teams"])
def listar_equipos_borrados(session: Session = Depends(get_session)):
    return listar_equipos_eliminados(session)

@app.post("/teams/{team_id}/restore", tags=["Teams"])
def restaurar_equipo_por_id(team_id: int, session: Session = Depends(get_session)):
    if restaurar_equipo(session, team_id):
        return {"message": "Equipo restaurado correctamente"}
    raise HTTPException(status_code=404, detail="No fue posible restaurar el equipo")

@app.get("/teams/search/", response_model=List[Team], tags=["Teams"])
def buscar_equipo(nombre: str = Query(..., min_length=1), session: Session = Depends(get_session)):
    return buscar_equipo_por_nombre(session, nombre)

@app.get("/teams/region/{region}", response_model=List[Team], tags=["Teams"])
def filtrar_equipos_por_region(region: str, session: Session = Depends(get_session)):
    equipos = filtrar_equipo_por_region(session, region)
    if not equipos:
        raise HTTPException(status_code=404, detail=f"No hay equipos registrados en la región {region}")
    return equipos

# --- RUTAS CON PARÁMETRO (al final)
@app.get("/teams/{team_id}", response_model=Team, tags=["Teams"])
def obtener_equipo_por_id(team_id: int, session: Session = Depends(get_session)):
    return obtener_equipo(session, team_id)

@app.put("/teams/{team_id}", response_model=Team, tags=["Teams"])
def actualizar_datos_equipo(team_id: int, obj: Team, session: Session = Depends(get_session)):
    return actualizar_equipo(session, team_id, obj)

@app.delete("/teams/{team_id}", tags=["Teams"])
def eliminar_equipo_por_id(team_id: int, session: Session = Depends(get_session)):
    if eliminar_equipo(session, team_id):
        return {"message": "Equipo eliminado correctamente"}
    raise HTTPException(status_code=404, detail="Equipo no encontrado")


# MATCHES  (orden: estáticas -> dinámicas)

@app.post("/matches/", response_model=MatchSummary, tags=["Matches"])
def crear_nueva_partida(obj: MatchSummary, session: Session = Depends(get_session)):
    return crear_resumen(session, obj)

@app.get("/matches/", response_model=List[MatchSummary], tags=["Matches"])
def listar_todas_las_partidas(
    skip: int = 0,
    limit: int = Query(10, le=100),
    include_deleted: bool = Query(False, description="Incluir eliminados lógicamente"),
    session: Session = Depends(get_session)
):
    return listar_resumenes(session, skip=skip, limit=limit, include_deleted=include_deleted)

# --- RUTAS ESTÁTICAS
@app.get("/matches/deleted", response_model=List[MatchSummary], tags=["Matches"])
def listar_partidas_borradas(session: Session = Depends(get_session)):
    return listar_resumenes_eliminados(session)

@app.post("/matches/{resumen_id}/restore", tags=["Matches"])
def restaurar_partida_por_id(resumen_id: int, session: Session = Depends(get_session)):
    if restaurar_resumen(session, resumen_id):
        return {"message": "Resumen restaurado correctamente"}
    raise HTTPException(status_code=404, detail="No fue posible restaurar el resumen")

@app.get("/matches/search/", response_model=List[MatchSummary], tags=["Matches"])
def buscar_partidas_por_etapa(etapa: str = Query(..., min_length=1), session: Session = Depends(get_session)):
    return buscar_resumen_por_etapa(session, etapa)

@app.get("/matches/winner/{team_id}", response_model=List[MatchSummary], tags=["Matches"])
def filtrar_partidas_por_ganador(team_id: int, session: Session = Depends(get_session)):
    partidas = filtrar_resumen_por_ganador(session, team_id)
    if not partidas:
        raise HTTPException(status_code=404, detail="No se encontraron partidas ganadas por este equipo")
    return partidas
