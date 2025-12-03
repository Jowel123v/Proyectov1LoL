from pathlib import Path
import csv

from sqlmodel import Session, select, delete

from utils.db import engine, crear_db
from data.models import Team, Player, Champion, MatchSummary, MatchChampionLink


# =========================
# RUTAS CSV
# =========================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data_raw"

TEAMS_CSV = DATA_DIR / "teams_worlds2024.csv"
PLAYERS_CSV = DATA_DIR / "players_worlds2024.csv"
CHAMPIONS_CSV = DATA_DIR / "champions_worlds2024.csv"
MATCHES_CSV = DATA_DIR / "matches_worlds2024.csv"


def _to_int(value: str) -> int:
    value = value.strip()
    return int(value) if value else 0


def _to_float(value: str) -> float:
    value = value.strip()
    return float(value) if value else 0.0


# =========================
# LIMPIAR TODO
# =========================

def clear_all(session: Session) -> None:
    # El orden importa por las FKs
    session.exec(delete(MatchChampionLink))
    session.exec(delete(MatchSummary))
    session.exec(delete(Player))
    session.exec(delete(Champion))
    session.exec(delete(Team))
    session.commit()
    print("🔁 Tablas limpiadas (MatchChampionLink, MatchSummary, Player, Champion, Team).")


# =========================
# SEED TEAMS
# =========================

def seed_teams(session: Session) -> None:
    print(f"Sembrando TEAMS desde {TEAMS_CSV} ...")

    with TEAMS_CSV.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f" - Filas leídas en teams CSV: {len(rows)}")

    for row in rows:
        team = Team(
            name=row["name"],
            region=row["region"],
            wins=_to_int(row["wins"]),
            losses=_to_int(row["losses"]),
            avg_kda=_to_float(row["avg_kda"]),
            favorite_champions=row.get("favorite_champions"),
        )
        session.add(team)

    session.commit()
    print("✔ Teams de Worlds 2024 sembrados.")


# =========================
# SEED PLAYERS
# =========================

def seed_players(session: Session) -> None:
    print(f"Sembrando PLAYERS desde {PLAYERS_CSV} ...")

    # Para mapear nombre de equipo -> id
    teams_by_name = {
        t.name: t.id for t in session.exec(select(Team)).all()
    }
    print(f" - Teams en BD: {len(teams_by_name)}")

    with PLAYERS_CSV.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f" - Filas leídas en players CSV: {len(rows)}")

    for row in rows:
        team_name = row.get("team_name")
        team_id = teams_by_name.get(team_name)

        player = Player(
            nickname=row["nickname"],
            real_name=row.get("real_name") or None,
            role=row["role"],
            country=row.get("country") or None,
            team_id=team_id,
        )
        session.add(player)

    session.commit()
    print("✔ Players de Worlds 2024 sembrados.")


# =========================
# SEED CHAMPIONS
# =========================

def seed_champions(session: Session) -> None:
    print(f"Sembrando CHAMPIONS desde {CHAMPIONS_CSV} ...")

    with CHAMPIONS_CSV.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f" - Filas leídas en champions CSV: {len(rows)}")

    for row in rows:
        champ = Champion(
            slug=row["slug"],
            name=row["name"],
            pick_rate=_to_float(row["pick_rate"]),
            ban_rate=_to_float(row["ban_rate"]),
            win_rate=_to_float(row["win_rate"]),
            kda=_to_float(row["kda"]),
        )
        session.add(champ)

    session.commit()
    print("✔ Champions de Worlds 2024 sembrados.")


# =========================
# SEED MATCHES (simple)
# =========================

def seed_matches(session: Session) -> None:
    print(f"Sembrando MATCHES desde {MATCHES_CSV} ...")

    teams_by_name = {
        t.name: t.id for t in session.exec(select(Team)).all()
    }

    with MATCHES_CSV.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f" - Filas leídas en matches CSV: {len(rows)}")

    for row in rows:
        team_a_id = teams_by_name.get(row["team_a"])
        team_b_id = teams_by_name.get(row["team_b"])
        winner_id = teams_by_name.get(row["winner"])

        match = MatchSummary(
            stage=row["stage"],
            team_a_id=team_a_id,
            team_b_id=team_b_id,
            winner_id=winner_id,
            avg_duration_min=_to_float(row["avg_duration_min"]),
            avg_kills_per_game=_to_float(row["avg_kills_per_game"]),
        )
        session.add(match)

    session.commit()
    print("✔ MatchSummary de Worlds 2024 sembrados.")


# =========================
# MAIN
# =========================

def main():
    print("Creando tablas (si no existen)...")
    crear_db()

    with Session(engine) as session:
        clear_all(session)
        seed_teams(session)
        seed_players(session)
        seed_champions(session)
        seed_matches(session)

    print("✅ Seed Worlds 2024 COMPLETADO.")


if __name__ == "__main__":
    main()
