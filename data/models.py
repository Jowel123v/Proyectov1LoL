from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

# BASE COMÚN: ID + SOFT DELETE

class TableBase(SQLModel):
    id: Optional[int] = Field(
        default=None,
        primary_key=True,
        sa_column_kwargs={"autoincrement": True},
    )
    # Campo interno para soft delete (no se muestra en JSON)
    is_deleted: bool = Field(default=False, exclude=True)

    class Config:
        extra = "forbid"
        validate_assignment = True

# TABLA INTERMEDIA N:M (CHAMPION <-> MATCHSUMMARY)

class MatchChampionLink(SQLModel, table=True):
    match_id: Optional[int] = Field(
        default=None,
        foreign_key="matchsummary.id",
        primary_key=True,
    )
    champion_id: Optional[int] = Field(
        default=None,
        foreign_key="champion.id",
        primary_key=True,
    )


# MODELOS PRINCIPALES (BD)

class Champion(TableBase, table=True):
    __tablename__ = "champion"

    slug: str = Field(index=True, unique=True, description="Identificador único del campeón")
    name: str = Field(min_length=1, max_length=100)
    pick_rate: float = Field(default=0.0)
    ban_rate: float = Field(default=0.0)
    win_rate: float = Field(default=0.0)
    kda: float = Field(default=0.0)

    # Relación N:M con MatchSummary
    matches: List["MatchSummary"] = Relationship(
        back_populates="champions",
        link_model=MatchChampionLink,
    )


class Team(TableBase, table=True):
    __tablename__ = "team"

    name: str = Field(index=True, unique=True, min_length=1, max_length=100)
    region: str = Field(min_length=1, max_length=50)
    wins: int = Field(default=0)
    losses: int = Field(default=0)
    avg_kda: float = Field(default=0.0)
    favorite_champions: Optional[str] = Field(
        default=None,
        description="Lista de campeones favoritos (ej: 'Ahri, Lee Sin')",
    )

    @property
    def win_rate(self):
        total_games = self.wins + self.losses
        if total_games == 0:
            return 0  # Evita la división por 0
        return (self.wins / total_games) * 100

    # Relaciones 1:N con MatchSummary
    matches_as_team_a: List["MatchSummary"] = Relationship(
        back_populates="team_a",
        sa_relationship_kwargs={"foreign_keys": "[MatchSummary.team_a_id]"},
    )
    matches_as_team_b: List["MatchSummary"] = Relationship(
        back_populates="team_b",
        sa_relationship_kwargs={"foreign_keys": "[MatchSummary.team_b_id]"},
    )
    matches_won: List["MatchSummary"] = Relationship(
        back_populates="winner",
        sa_relationship_kwargs={"foreign_keys": "[MatchSummary.winner_id]"},
    )
    players: List["Player"] = Relationship(back_populates="team")


class MatchSummary(TableBase, table=True):
    __tablename__ = "matchsummary"

    # Info básica
    stage: str = Field(
        min_length=1,
        max_length=100,
        description="Etapa: Play-Ins, Groups, Quarters, Semis, Finals, etc.",
    )

    # Relaciones con equipos
    team_a_id: Optional[int] = Field(default=None, foreign_key="team.id")
    team_b_id: Optional[int] = Field(default=None, foreign_key="team.id")
    winner_id: Optional[int] = Field(default=None, foreign_key="team.id")

    # Datos de rendimiento
    avg_duration_min: float = Field(default=0.0)
    avg_kills_per_game: float = Field(default=0.0)

    #  Relaciones inversas (para 1:N con Team) CON foreign_keys explícitos
    team_a: Optional[Team] = Relationship(
        back_populates="matches_as_team_a",
        sa_relationship_kwargs={"foreign_keys": "[MatchSummary.team_a_id]"},
    )
    team_b: Optional[Team] = Relationship(
        back_populates="matches_as_team_b",
        sa_relationship_kwargs={"foreign_keys": "[MatchSummary.team_b_id]"},
    )
    winner: Optional[Team] = Relationship(
        back_populates="matches_won",
        sa_relationship_kwargs={"foreign_keys": "[MatchSummary.winner_id]"},
    )

    # N:M con Champion
    champions: List[Champion] = Relationship(
        back_populates="matches",
        link_model=MatchChampionLink,
    )


# PLAYER MODELO

class Player(TableBase, table=True):
    __tablename__ = "player"

    nickname: str = Field(index=True, min_length=1, max_length=50)
    real_name: Optional[str] = Field(default=None, max_length=100)
    role: str = Field(
        min_length=2,
        max_length=10,
        description="Rol: TOP, JNG, MID, ADC, SUP",
    )
    country: Optional[str] = Field(default=None, max_length=50)

    # Relación con Team
    team_id: Optional[int] = Field(default=None, foreign_key="team.id")
    team: Optional[Team] = Relationship(back_populates="players")
    kda: float = Field(default=0.0, description="Promedio KDA del jugador")


__all__ = [
    "TableBase",
    "Champion",
    "Team",
    "MatchSummary",
    "MatchChampionLink",
    "Player",
]
