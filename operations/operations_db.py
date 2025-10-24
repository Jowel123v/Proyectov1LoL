from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from data.models import (
    Champion,
    Team,
    MatchSummary,
    MatchChampionLink,
)


# HELPERS


def _apply_active_filter(model, include_deleted: bool = False):
    """Condición para incluir/excluir eliminados lógicamente."""
    if include_deleted:
        return True
    return model.is_deleted == False  # noqa: E712


def _handle_exception(session: Session, exc: Exception, message: str):
    """Rollback y excepción HTTP unificada."""
    session.rollback()
    raise HTTPException(status_code=500, detail=f"{message}. Error: {str(exc)}")


def _created_payload(obj) -> Dict[str, Any]:
    """
    Respuesta para CREATE:
    - oculta 'id' y 'is_deleted' (aunque is_deleted ya está oculto por el modelo)
    """
    return obj.dict(exclude={"id", "is_deleted"})



# CHAMPIONS (CRUD + BÚSQUEDA + HISTORIAL)


def crear_campeon(session: Session, obj: Champion) -> Dict[str, Any]:
    try:
        obj.id = None  # ignorar cualquier id entrante
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return _created_payload(obj)  # sin id ni is_deleted
    except SQLAlchemyError as e:
        _handle_exception(session, e, "Error al crear el campeón")


def listar_campeones(
    session: Session,
    skip: int = 0,
    limit: int = 10,
    include_deleted: bool = False,
) -> List[Champion]:
    try:
        q = select(Champion).where(_apply_active_filter(Champion, include_deleted)).offset(skip).limit(limit)
        return session.exec(q).all()
    except SQLAlchemyError as e:
        _handle_exception(session, e, "Error al listar los campeones")


def listar_campeones_eliminados(session: Session) -> List[Champion]:
    try:
        q = select(Champion).where(Champion.is_deleted == True)  # noqa: E712
        return session.exec(q).all()
    except SQLAlchemyError as e:
        _handle_exception(session, e, "Error al listar campeones eliminados")


def restaurar_campeon(session: Session, champion_id: int) -> bool:
    try:
        obj = session.get(Champion, champion_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Campeón no encontrado")
        if not obj.is_deleted:
            raise HTTPException(status_code=400, detail="El campeón no está eliminado")
        obj.is_deleted = False
        session.add(obj)
        session.commit()
        return True
    except SQLAlchemyError as e:
        _handle_exception(session, e, "Error al restaurar el campeón")


def buscar_campeon_por_nombre(session: Session, nombre: str) -> List[Champion]:
    """Búsqueda por nombre (parcial)."""
    try:
        q = select(Champion).where(
            Champion.name.ilike(f"%{nombre}%"), Champion.is_deleted == False  # noqa: E712
        )
        resultados = session.exec(q).all()
        if not resultados:
            raise HTTPException(status_code=404, detail=f"No se encontraron campeones que contengan '{nombre}'")
        return resultados
    except SQLAlchemyError as e:
        _handle_exception(session, e, "Error al buscar campeones por nombre")


def filtrar_campeones_por_winrate(session: Session, min_winrate: float = 0.0) -> List[Champion]:
    """Campeones con win_rate >= umbral."""
    try:
        if min_winrate < 0:
            raise HTTPException(status_code=400, detail="min_winrate no puede ser negativo")
        q = select(Champion).where(
            Champion.win_rate >= min_winrate, Champion.is_deleted == False  # noqa: E712
        )
        return session.exec(q).all()
    except SQLAlchemyError as e:
        _handle_exception(session, e, "Error al filtrar campeones por win rate")


def obtener_campeon(session: Session, champion_id: int) -> Champion:
    try:
        obj = session.get(Champion, champion_id)
        if not obj or obj.is_deleted:
            raise HTTPException(status_code=404, detail="Campeón no encontrado o eliminado")
        return obj
    except SQLAlchemyError as e:
        _handle_exception(session, e, "Error al obtener el campeón")


def actualizar_campeon(session: Session, champion_id: int, obj_update: Champion) -> Champion:
    try:
        obj = session.get(Champion, champion_id)
        if not obj or obj.is_deleted:
            raise HTTPException(status_code=404, detail="Campeón no encontrado o eliminado")

        data = obj_update.dict(exclude_unset=True)
        data.pop("id", None)
        data.pop("is_deleted", None)

        for k, v in data.items():
            setattr(obj, k, v)
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj
    except SQLAlchemyError as e:
        _handle_exception(session, e, "Error al actualizar el campeón")


def eliminar_campeon(session: Session, champion_id: int) -> bool:
    try:
        obj = session.get(Champion, champion_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Campeón no encontrado")
        if obj.is_deleted:
            raise HTTPException(status_code=400, detail="El campeón ya estaba eliminado")
        obj.is_deleted = True
        session.add(obj)
        session.commit()
        return True
    except SQLAlchemyError as e:
        _handle_exception(session, e, "Error al eliminar el campeón")



# TEAMS (CRUD + FILTROS + HISTORIAL)


def crear_equipo(session: Session, obj: Team) -> Dict[str, Any]:
    try:
        obj.id = None
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return _created_payload(obj)  # sin id ni is_deleted
    except SQLAlchemyError as e:
        _handle_exception(session, e, "Error al crear el equipo")


def listar_equipos(
    session: Session,
    skip: int = 0,
    limit: int = 10,
    include_deleted: bool = False,
) -> List[Team]:
    try:
        q = select(Team).where(_apply_active_filter(Team, include_deleted)).offset(skip).limit(limit)
        return session.exec(q).all()
    except SQLAlchemyError as e:
        _handle_exception(session, e, "Error al listar equipos")


def listar_equipos_eliminados(session: Session) -> List[Team]:
    try:
        q = select(Team).where(Team.is_deleted == True)  # noqa: E712
        return session.exec(q).all()
    except SQLAlchemyError as e:
        _handle_exception(session, e, "Error al listar equipos eliminados")


def restaurar_equipo(session: Session, team_id: int) -> bool:
    try:
        obj = session.get(Team, team_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Equipo no encontrado")
        if not obj.is_deleted:
            raise HTTPException(status_code=400, detail="El equipo no está eliminado")
        obj.is_deleted = False
        session.add(obj)
        session.commit()
        return True
    except SQLAlchemyError as e:
        _handle_exception(session, e, "Error al restaurar el equipo")


def buscar_equipo_por_nombre(session: Session, nombre: str) -> List[Team]:
    """Búsqueda por nombre (parcial)."""
    try:
        q = select(Team).where(Team.name.ilike(f"%{nombre}%"), Team.is_deleted == False)  # noqa: E712
        resultados = session.exec(q).all()
        if not resultados:
            raise HTTPException(status_code=404, detail=f"No se encontró ningún equipo con '{nombre}'")
        return resultados
    except SQLAlchemyError as e:
        _handle_exception(session, e, "Error al buscar equipo por nombre")


def filtrar_equipo_por_region(session: Session, region: str) -> List[Team]:
    """Filtra equipos por región (LCK, LPL, etc.)."""
    try:
        q = select(Team).where(Team.region == region, Team.is_deleted == False)  # noqa: E712
        return session.exec(q).all()
    except SQLAlchemyError as e:
        _handle_exception(session, e, "Error al filtrar equipos por región")


def obtener_equipo(session: Session, team_id: int) -> Team:
    try:
        obj = session.get(Team, team_id)
        if not obj or obj.is_deleted:
            raise HTTPException(status_code=404, detail="Equipo no encontrado o eliminado")
        return obj
    except SQLAlchemyError as e:
        _handle_exception(session, e, "Error al obtener equipo")


def actualizar_equipo(session: Session, team_id: int, obj_update: Team) -> Team:
    try:
        obj = session.get(Team, team_id)
        if not obj or obj.is_deleted:
            raise HTTPException(status_code=404, detail="Equipo no encontrado o eliminado")

        data = obj_update.dict(exclude_unset=True)
        data.pop("id", None)
        data.pop("is_deleted", None)

        for k, v in data.items():
            setattr(obj, k, v)
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj
    except SQLAlchemyError as e:
        _handle_exception(session, e, "Error al actualizar equipo")


def eliminar_equipo(session: Session, team_id: int) -> bool:
    try:
        obj = session.get(Team, team_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Equipo no encontrado")
        if obj.is_deleted:
            raise HTTPException(status_code=400, detail="El equipo ya estaba eliminado")
        obj.is_deleted = True
        session.add(obj)
        session.commit()
        return True
    except SQLAlchemyError as e:
        _handle_exception(session, e, "Error al eliminar equipo")



# MATCH SUMMARY (CRUD + BÚSQUEDA + HISTORIAL)


def crear_resumen(session: Session, obj: MatchSummary) -> Dict[str, Any]:
    try:
        obj.id = None
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return _created_payload(obj)  # sin id ni is_deleted
    except SQLAlchemyError as e:
        _handle_exception(session, e, "Error al crear el resumen de partida")


def listar_resumenes(
    session: Session,
    skip: int = 0,
    limit: int = 10,
    include_deleted: bool = False,
) -> List[MatchSummary]:
    try:
        q = select(MatchSummary).where(_apply_active_filter(MatchSummary, include_deleted)).offset(skip).limit(limit)
        return session.exec(q).all()
    except SQLAlchemyError as e:
        _handle_exception(session, e, "Error al listar los resúmenes")


def listar_resumenes_eliminados(session: Session) -> List[MatchSummary]:
    try:
        q = select(MatchSummary).where(MatchSummary.is_deleted == True)  # noqa: E712
        return session.exec(q).all()
    except SQLAlchemyError as e:
        _handle_exception(session, e, "Error al listar resúmenes eliminados")


def restaurar_resumen(session: Session, resumen_id: int) -> bool:
    try:
        obj = session.get(MatchSummary, resumen_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Resumen no encontrado")
        if not obj.is_deleted:
            raise HTTPException(status_code=400, detail="El resumen no está eliminado")
        obj.is_deleted = False
        session.add(obj)
        session.commit()
        return True
    except SQLAlchemyError as e:
        _handle_exception(session, e, "Error al restaurar resumen")


def buscar_resumen_por_etapa(session: Session, etapa: str) -> List[MatchSummary]:
    """Busca partidas por fase/etapa (Worlds, Playoffs, etc.)."""
    try:
        q = select(MatchSummary).where(
            MatchSummary.stage.ilike(f"%{etapa}%"), MatchSummary.is_deleted == False  # noqa: E712
        )
        resultados = session.exec(q).all()
        if not resultados:
            raise HTTPException(status_code=404, detail=f"No se encontraron partidas en la etapa '{etapa}'")
        return resultados
    except SQLAlchemyError as e:
        _handle_exception(session, e, "Error al buscar resúmenes por etapa")


def filtrar_resumen_por_ganador(session: Session, team_id: int) -> List[MatchSummary]:
    """Partidas ganadas por un equipo específico."""
    try:
        q = select(MatchSummary).where(
            MatchSummary.winner_id == team_id,
            MatchSummary.is_deleted == False,  # noqa: E712
        )
        return session.exec(q).all()
    except SQLAlchemyError as e:
        _handle_exception(session, e, "Error al filtrar resúmenes por ganador")



# (Opcional) N:M utilities si las llegas a exponer como endpoints


def obtener_campeones_de_match(session: Session, match_id: int) -> List[Champion]:
    """Campeones asociados a un match (solo activos)."""
    try:
        match = session.get(MatchSummary, match_id)
        if not match or match.is_deleted:
            raise HTTPException(status_code=404, detail="Match no encontrado o eliminado")
        return [c for c in match.champions if not c.is_deleted]
    except SQLAlchemyError as e:
        _handle_exception(session, e, "Error al obtener campeones del match")
