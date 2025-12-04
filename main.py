from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session
from typing import List
from utils.db import get_session, crear_db
from data.models import Champion, Team, MatchSummary, Player
from operations.operations_db import (
    crear_campeon, listar_campeones, listar_campeones_eliminados, restaurar_campeon,
    buscar_campeon_por_nombre, filtrar_campeones_por_winrate, obtener_campeon, actualizar_campeon, eliminar_campeon,
    crear_equipo, listar_equipos, listar_equipos_eliminados, restaurar_equipo,
    buscar_equipo_por_nombre, filtrar_equipo_por_region, obtener_equipo, actualizar_equipo, eliminar_equipo,
    crear_resumen, listar_resumenes, listar_resumenes_eliminados, restaurar_resumen,
    buscar_resumen_por_etapa, filtrar_resumen_por_ganador,
    crear_jugador, listar_jugadores, listar_jugadores_eliminados, restaurar_jugador,
    buscar_jugadores_por_nickname, filtrar_jugadores_por_rol, filtrar_jugadores_por_equipo,
    obtener_jugador, actualizar_jugador, eliminar_jugador,
)

app = FastAPI(
    title="LoL Worlds API",
    description="API para gestión y análisis de campeones, equipos y partidas del Mundial de League of Legends.",
    version="1.1",
)

# Templates Jinja22
templates = Jinja2Templates(directory="templates")

# Archivos estáticos (CSS, imágenes, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
def on_startup():
    crear_db()

@app.get("/health", tags=["Root"])
def health():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse, tags=["Front"])
def home(
        request: Request,
        session: Session = Depends(get_session),
):
    """Dashboard principal con todas las secciones integradas"""

    # Cargar TODOS los datos
    equipos = listar_equipos(session, skip=0, limit=100, include_deleted=False)
    jugadores = listar_jugadores(session, skip=0, limit=200, include_deleted=False)
    campeones = listar_campeones(session, skip=0, limit=200, include_deleted=False)
    matches = listar_resumenes(session, skip=0, limit=500, include_deleted=False)

    # Agregar win_rate calculado a cada equipo para que Jinja2 pueda accederlo
    equipos_con_winrate = []
    total_team_win_rate = 0.0
    total_team_duration = 0.0
    teams_with_duration = 0
    
    for equipo in equipos:
        # Convertir a dict y agregar win_rate calculado
        equipo_dict = equipo.model_dump()
        total_games = equipo.wins + equipo.losses
        win_rate = (equipo.wins / total_games * 100) if total_games > 0 else 0.0
        equipo_dict['win_rate'] = win_rate
        total_team_win_rate += win_rate
        
        # Calcular duración promedio de las partidas de este equipo
        team_matches = [m for m in matches if m.team_a_id == equipo.id or m.team_b_id == equipo.id]
        if len(team_matches) > 0:
            team_avg_duration = sum(m.avg_duration_min for m in team_matches) / len(team_matches)
            equipo_dict['avg_duration'] = f"{team_avg_duration:.1f} min"
            total_team_duration += team_avg_duration
            teams_with_duration += 1
        else:
            equipo_dict['avg_duration'] = "-"
        
        equipos_con_winrate.append(equipo_dict)

    # Calcular promedios de campeones
    avg_champion_pick_rate = 0.0
    avg_champion_win_rate = 0.0
    if len(campeones) > 0:
        total_pick_rate = sum(c.pick_rate for c in campeones)
        total_win_rate = sum(c.win_rate for c in campeones)
        avg_champion_pick_rate = (total_pick_rate / len(campeones)) * 100
        avg_champion_win_rate = (total_win_rate / len(campeones)) * 100

    # Calcular promedios de equipos
    avg_team_win_rate = (total_team_win_rate / len(equipos)) if len(equipos) > 0 else 0.0
    avg_team_duration = "-"
    
    if teams_with_duration > 0:
        avg_team_duration = f"{(total_team_duration / teams_with_duration):.1f} min"

    # Calcular promedios de jugadores (basados en el KDA promedio de sus equipos)
    # Como no tenemos win_rate ni KDA individual por jugador, calculamos el promedio de los equipos
    total_player_kda = 0.0
    players_with_team = 0
    
    for jugador in jugadores:
        if jugador.team_id:
            # Buscar el equipo correspondiente
            equipo = next((e for e in equipos if e.id == jugador.team_id), None)
            if equipo:
                total_player_kda += equipo.avg_kda
                players_with_team += 1

    avg_player_win_rate = avg_team_win_rate  # Usamos el mismo promedio que equipos
    avg_player_kda = (total_player_kda / players_with_team) if players_with_team > 0 else 0.0

    # Calcular estadísticas
    stats = {
        "teams": len(equipos),
        "players": len(jugadores),
        "champions": len(campeones),
        "matches": len(matches),
        "avg_champion_pick_rate": avg_champion_pick_rate,
        "avg_champion_win_rate": avg_champion_win_rate,
        "avg_team_win_rate": avg_team_win_rate,
        "avg_team_duration": avg_team_duration,
        "avg_player_win_rate": avg_player_win_rate,
        "avg_player_kda": avg_player_kda,
    }

    # Agregar nombres de equipos a los matches para la visualización
    matches_with_names = []
    for match in matches:
        match_dict = match.model_dump()
        
        # Buscar los nombres de los equipos
        team_a = next((e for e in equipos if e.id == match.team_a_id), None)
        team_b = next((e for e in equipos if e.id == match.team_b_id), None)
        winner = next((e for e in equipos if e.id == match.winner_id), None)
        
        match_dict['team_a_name'] = team_a.name if team_a else f"Team {match.team_a_id}"
        match_dict['team_b_name'] = team_b.name if team_b else f"Team {match.team_b_id}"
        match_dict['winner_name'] = winner.name if winner else f"Team {match.winner_id}"
        
        matches_with_names.append(match_dict)

    # Retornar la respuesta con los cálculos de los promedios
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "stats": stats,
            "equipos": equipos_con_winrate,
            "jugadores": jugadores,
            "campeones": campeones,
            "matches": matches_with_names,
        },
    )

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


# MATCHES

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


# PLAYERS

@app.post("/players/", response_model=Player, tags=["Players"])
def crear_nuevo_jugador(obj: Player, session: Session = Depends(get_session)):
    return crear_jugador(session, obj)


@app.get("/players/", response_model=List[Player], tags=["Players"])
def listar_todos_los_jugadores(
    skip: int = 0,
    limit: int = Query(10, le=100),
    include_deleted: bool = Query(False, description="Incluir eliminados lógicamente"),
    session: Session = Depends(get_session),
):
    return listar_jugadores(session, skip=skip, limit=limit, include_deleted=include_deleted)

@app.get("/players/deleted", response_model=List[Player], tags=["Players"])
def listar_jugadores_borrados(session: Session = Depends(get_session)):
    """Lista solo los jugadores con soft delete (is_deleted = True)."""
    return listar_jugadores_eliminados(session)


@app.post("/players/{player_id}/restore", tags=["Players"])
def restaurar_jugador_por_id(player_id: int, session: Session = Depends(get_session)):
    """Restaura un jugador eliminado (is_deleted pasa a False)."""
    if restaurar_jugador(session, player_id):
        return {"message": "Jugador restaurado correctamente"}
    raise HTTPException(status_code=404, detail="No fue posible restaurar el jugador")


@app.get("/players/search/", response_model=List[Player], tags=["Players"])
def buscar_jugadores(
    nickname: str = Query(..., min_length=1),
    session: Session = Depends(get_session),
):
    return buscar_jugadores_por_nickname(session, nickname)


@app.get("/players/role/{role}", response_model=List[Player], tags=["Players"])
def filtrar_jugadores_por_role(role: str, session: Session = Depends(get_session)):
    jugadores = filtrar_jugadores_por_rol(session, role)
    if not jugadores:
        raise HTTPException(status_code=404, detail="No se encontraron jugadores para ese rol")
    return jugadores


@app.get("/players/team/{team_id}", response_model=List[Player], tags=["Players"])
def filtrar_jugadores_por_team(team_id: int, session: Session = Depends(get_session)):
    jugadores = filtrar_jugadores_por_equipo(session, team_id)
    if not jugadores:
        raise HTTPException(status_code=404, detail="No se encontraron jugadores para ese equipo")
    return jugadores


# --- RUTAS CON PARÁMETRO (CRUD por id)

@app.get("/players/{player_id}", response_model=Player, tags=["Players"])
def obtener_jugador_por_id(player_id: int, session: Session = Depends(get_session)):
    return obtener_jugador(session, player_id)


@app.put("/players/{player_id}", response_model=Player, tags=["Players"])
def actualizar_datos_jugador(
    player_id: int,
    obj: Player,
    session: Session = Depends(get_session),
):
    return actualizar_jugador(session, player_id, obj)


@app.delete("/players/{player_id}", tags=["Players"])
def eliminar_jugador_por_id(player_id: int, session: Session = Depends(get_session)):
    if eliminar_jugador(session, player_id):
        return {"message": "Jugador eliminado correctamente"}
    raise HTTPException(status_code=404, detail="Jugador no encontrado")
