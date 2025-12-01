from typing import Optional
from pydantic import BaseModel, Field

# CHAMPION

class ChampionBase(BaseModel):
    slug: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=100)
    pick_rate: float = 0.0
    ban_rate: float = 0.0
    win_rate: float = 0.0
    kda: float = 0.0


class ChampionCreate(ChampionBase):
    pass


class ChampionUpdate(BaseModel):
    slug: Optional[str] = Field(default=None, min_length=1, max_length=100)
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    pick_rate: Optional[float] = None
    ban_rate: Optional[float] = None
    win_rate: Optional[float] = None
    kda: Optional[float] = None


class ChampionRead(ChampionBase):
    id: int

# TEAM

class TeamBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    region: str = Field(min_length=1, max_length=50)
    wins: int = 0
    losses: int = 0
    avg_kda: float = 0.0
    favorite_champions: Optional[str] = None


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    region: Optional[str] = Field(default=None, min_length=1, max_length=50)
    wins: Optional[int] = None
    losses: Optional[int] = None
    avg_kda: Optional[float] = None
    favorite_champions: Optional[str] = None


class TeamRead(TeamBase):
    id: int

# MATCH SUMMARY

class MatchSummaryBase(BaseModel):
    stage: str = Field(min_length=1, max_length=100)
    team_a_id: Optional[int]
    team_b_id: Optional[int]
    winner_id: Optional[int]
    avg_duration_min: float = 0.0
    avg_kills_per_game: float = 0.0


class MatchSummaryCreate(MatchSummaryBase):
    pass


class MatchSummaryUpdate(BaseModel):
    stage: Optional[str] = Field(default=None, min_length=1, max_length=100)
    team_a_id: Optional[int] = None
    team_b_id: Optional[int] = None
    winner_id: Optional[int] = None
    avg_duration_min: Optional[float] = None
    avg_kills_per_game: Optional[float] = None


class MatchSummaryRead(MatchSummaryBase):
    id: int

# LINK CHAMPION <-> MATCH

class MatchChampionLinkIn(BaseModel):
    match_id: int
    champion_id: int

