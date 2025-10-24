from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship



# Base común: ID autoincremental + eliminación lógica oculta

class TableBase(SQLModel):
    id: Optional[int] = Field(
        default=None,
        primary_key=True,
        sa_column_kwargs={"autoincrement": True}
    )
    # Campo interno para soft delete (no se muestra en respuestas JSON)
    is_deleted: bool = Field(default=False, exclude=True)

    class Config:
        extra = "forbid"
        validate_assignment = True



# TABLA INTERMEDIA N:M Champion <-> MatchSummary

class MatchChampionLink(SQLModel, table=True):
    match_id: Optional[int] = Field(default=None, foreign_key="matchsummary.id", primary_key=True)
    champion_id: Optional[int] = Field(default=None, foreign_key="champion.id", primary_key=True)



# MODELO 1: CHAMPION

class Champion(TableBase, table=True):
    slug: str
    name: str
    pick_rate: float = 0.0
    ban_rate: float = 0.0
    win_rate: float = 0.0
    kda: float = 0.0

    # N:M con MatchSummary (campeones usados en partidas)
    matches: List["MatchSummary"] = Relationship(back_populates="champions", link_model=MatchChampionLink)



# MODELO 2: TEAM

class Team(TableBase, table=True):
    name: str
    region: str
    wins: int = 0
    losses: int = 0
    avg_kda: float = 0.0
    favorite_champions: Optional[str] = None  # CSV simple: "Ahri, Lee Sin"

    # 1:N con MatchSummary (un equipo participa en muchas partidas)
    matches_as_team_a: List["MatchSummary"] = Relationship(back_populates="team_a", sa_relationship_kwargs={"foreign_keys": "[MatchSummary.team_a_id]"})
    matches_as_team_b: List["MatchSummary"] = Relationship(back_populates="team_b", sa_relationship_kwargs={"foreign_keys": "[MatchSummary.team_b_id]"})
    matches_won: List["MatchSummary"] = Relationship(back_populates="winner", sa_relationship_kwargs={"foreign_keys": "[MatchSummary.winner_id]"})



# MODELO 3: MATCHSUMMARY

class MatchSummary(TableBase, table=True):
    stage: str  # ej. "Worlds 2025", "Play-In", etc.

    # Relaciones 1:N con Team
    team_a_id: Optional[int] = Field(default=None, foreign_key="team.id")
    team_b_id: Optional[int] = Field(default=None, foreign_key="team.id")
    winner_id: Optional[int] = Field(default=None, foreign_key="team.id")

    # Datos de rendimiento
    avg_duration_min: float = 0.0
    avg_kills_per_game: float = 0.0

    # Relaciones inversas (para 1:N con Team)
    team_a: Optional[Team] = Relationship(back_populates="matches_as_team_a", sa_relationship_kwargs={"foreign_keys": "[MatchSummary.team_a_id]"})
    team_b: Optional[Team] = Relationship(back_populates="matches_as_team_b", sa_relationship_kwargs={"foreign_keys": "[MatchSummary.team_b_id]"})
    winner: Optional[Team] = Relationship(back_populates="matches_won", sa_relationship_kwargs={"foreign_keys": "[MatchSummary.winner_id]"})

    # N:M con Champion
    champions: List[Champion] = Relationship(back_populates="matches", link_model=MatchChampionLink)
