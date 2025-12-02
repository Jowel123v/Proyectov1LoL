import csv
from pathlib import Path

from sqlmodel import Session, select

from utils.db import engine, crear_db
from data.models import Team, Player, Champion, MatchSummary


# RUTAS DE LOS CSV

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data_raw"

TEAMS_CSV = DATA_DIR / "teams_worlds2024.csv"
PLAYERS_CSV = DATA_DIR / "players_worlds2024.csv"
CHAMPIONS_CSV = DATA_DIR / "champions_worlds2024.csv"
MATCHES_CSV = DATA_DIR / "matches_worlds2024.csv"


# HELPERS

def _to_int(value, default=0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (ValueError, TypeError):
        return default


def _to_float(value, default=0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


# SEED TEAMS

def seed_teams(session: Session) -> None:
    """Carga equipos desde teams_worlds2024.csv a la tabla Team."""
    if session.exec(select(Team)).first():
        print("Teams ya existen, no se vuelven a crear.")
        return

    if not TEAMS_CSV.exists():
        raise FileNotFoundError(f"No se encontró {TEAMS_CSV}")

    with TEAMS_CSV.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            name = row["name"]
            region = row["region"]

            if not name:
                continue

            # Evitar duplicados por nombre
            existing = session.exec(
                select(Team).where(Team.name == name)
            ).first()
            if existing:
                continue

            wins = _to_int(row["wins"])
            losses = _to_int(row["losses"])
            avg_kda = _to_float(row["avg_kda"])
            favorite_champions = row.get("favorite_champions") or None

            team = Team(
                name=name,
                region=region,
                wins=wins,
                losses=losses,
                avg_kda=avg_kda,
                favorite_champions=favorite_champions,
            )
            session.add(team)

    session.commit()
    print("✔ Teams de Worlds 2024 sembrados correctamente.")


# SEED PLAYERS

def seed_players(session: Session) -> None:
    """Carga jugadores desde players_worlds2024.csv a la tabla Player."""
    if session.exec(select(Player)).first():
        print("Players ya existen, no se vuelven a crear.")
        return

    if not PLAYERS_CSV.exists():
        raise FileNotFoundError(f"No se encontró {PLAYERS_CSV}")

    # Cache de equipos por nombre para no consultar todo el tiempo
    teams_cache: dict[str, Team] = {}

    def get_team_by_name(team_name: str) -> Team | None:
        if not team_name:
            return None
        if team_name in teams_cache:
            return teams_cache[team_name]
        team = session.exec(
            select(Team).where(Team.name == team_name)
        ).first()
        if team:
            teams_cache[team_name] = team
        return team

    with PLAYERS_CSV.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            nickname = row["nickname"]
            real_name = row.get("real_name") or None
            role = row.get("role") or "UNK"
            country = row.get("country") or None
            team_name = row.get("team_name") or ""

            if not nickname:
                continue

            team = get_team_by_name(team_name)
            team_id = team.id if team else None

            player = Player(
                nickname=nickname,
                real_name=real_name,
                role=role,
                country=country,
                team_id=team_id,
            )
            session.add(player)

    session.commit()
    print("✔ Players de Worlds 2024 sembrados correctamente.")


# SEED CHAMPIONS

def seed_champions(session: Session) -> None:
    """Carga campeones desde champions_worlds2024.csv a la tabla Champion."""
    if session.exec(select(Champion)).first():
        print("Champions ya existen, no se vuelven a crear.")
        return

    if not CHAMPIONS_CSV.exists():
        raise FileNotFoundError(f"No se encontró {CHAMPIONS_CSV}")

    with CHAMPIONS_CSV.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            slug = row["slug"]
            name = row["name"]

            if not name:
                continue

            # Evitar duplicados por nombre
            existing = session.exec(
                select(Champion).where(Champion.name == name)
            ).first()
            if existing:
                continue

            pick_rate = _to_float(row["pick_rate"])
            ban_rate = _to_float(row["ban_rate"])
            win_rate = _to_float(row["win_rate"])
            kda = _to_float(row["kda"])

            # Si quisieras recalcular slug:
            # slug = name.lower().replace(" ", "")

            champ = Champion(
                slug=slug,
                name=name,
                pick_rate=pick_rate,
                ban_rate=ban_rate,
                win_rate=win_rate,
                kda=kda,
            )
            session.add(champ)

    session.commit()
    print("✔ Champions de Worlds 2024 sembrados correctamente.")

# SEED MATCHES

def seed_matches(session: Session) -> None:
    """Carga partidas desde matches_worlds2024.csv a la tabla MatchSummary."""
    if session.exec(select(MatchSummary)).first():
        print("MatchSummary ya tiene datos, no se vuelven a crear.")
        return

    if not MATCHES_CSV.exists():
        raise FileNotFoundError(f"No se encontró {MATCHES_CSV}")

    # Cache de equipos por nombre
    teams_cache: dict[str, Team] = {}

    def get_team_by_name(team_name: str) -> Team | None:
        if not team_name:
            return None
        if team_name in teams_cache:
            return teams_cache[team_name]
        team = session.exec(
            select(Team).where(Team.name == team_name)
        ).first()
        if team:
            teams_cache[team_name] = team
        return team

    with MATCHES_CSV.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            stage = row["stage"]
            team_a_name = row["team_a_name"]
            team_b_name = row["team_b_name"]
            winner_name = row["winner_name"]

            team_a = get_team_by_name(team_a_name)
            team_b = get_team_by_name(team_b_name)
            winner = get_team_by_name(winner_name)

            # Si algún equipo no se encuentra, ignoramos ese registro
            if not team_a or not team_b or not winner:
                print(f"⚠ No se encontró algún equipo para la fila: {row}")
                continue

            avg_duration_min = _to_float(row["avg_duration_min"])
            avg_kills_per_game = _to_float(row["avg_kills_per_game"])

            match = MatchSummary(
                stage=stage,
                team_a_id=team_a.id,
                team_b_id=team_b.id,
                winner_id=winner.id,
                avg_duration_min=avg_duration_min,
                avg_kills_per_game=avg_kills_per_game,
            )
            session.add(match)

    session.commit()
    print("✔ MatchSummary de Worlds 2024 sembrados correctamente.")


# =========================
# MAIN
# =========================

def main() -> None:
    print("Creando tablas (si no existen)...")
    crear_db()

    with Session(engine) as session:
        seed_teams(session)
        seed_players(session)
        seed_champions(session)
        seed_matches(session)

    print("Worlds 2024 completado.")


if __name__ == "__main__":
    main()
