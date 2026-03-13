from __future__ import annotations

from datetime import datetime

from safrs import SAFRSBase
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from .db import Base


class ChessTournamentValidationError(ValueError):
    pass


class Tournament(SAFRSBase, Base):
    __tablename__ = "tournaments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(24), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    city: Mapped[str] = mapped_column(String(80), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    player_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pairing_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reported_pairing_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    players: Mapped[list["Player"]] = relationship(
        back_populates="tournament",
        passive_deletes=True,
    )
    pairings: Mapped[list["Pairing"]] = relationship(
        back_populates="tournament",
        passive_deletes=True,
    )


class Player(SAFRSBase, Base):
    __tablename__ = "players"
    __table_args__ = (
        UniqueConstraint(
            "tournament_id",
            "full_name",
            name="uq_players_tournament_full_name",
        ),
        UniqueConstraint(
            "tournament_id",
            "federation_id",
            name="uq_players_tournament_federation_id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    federation_id: Mapped[str] = mapped_column(String(32), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, default=1200, nullable=False)
    seed_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    tournament_id: Mapped[int] = mapped_column(
        ForeignKey("tournaments.id", ondelete="CASCADE"),
        nullable=False,
    )

    tournament: Mapped[Tournament] = relationship(back_populates="players")
    white_pairings: Mapped[list["Pairing"]] = relationship(
        "Pairing",
        back_populates="white_player",
        foreign_keys="Pairing.white_player_id",
        passive_deletes=True,
    )
    black_pairings: Mapped[list["Pairing"]] = relationship(
        "Pairing",
        back_populates="black_player",
        foreign_keys="Pairing.black_player_id",
        passive_deletes=True,
    )

    @validates("tournament_id")
    def validate_tournament(self, key: str, value: int | None) -> int:
        if value is None:
            raise ChessTournamentValidationError(f"{key} is required")
        return value


class PairingStatus(SAFRSBase, Base):
    __tablename__ = "pairing_statuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    is_reported: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    pairings: Mapped[list["Pairing"]] = relationship(
        back_populates="status",
        passive_deletes=True,
    )


class Pairing(SAFRSBase, Base):
    __tablename__ = "pairings"
    __table_args__ = (
        UniqueConstraint(
            "tournament_id",
            "round_number",
            "board_number",
            name="uq_pairings_tournament_round_board",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pairing_code: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    board_number: Mapped[int] = mapped_column(Integer, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    reported_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    result_summary: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status_code: Mapped[str] = mapped_column(String(32), default="", nullable=False)
    is_reported: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reported_value: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tournament_id: Mapped[int] = mapped_column(
        ForeignKey("tournaments.id", ondelete="CASCADE"),
        nullable=False,
    )
    white_player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="RESTRICT"),
        nullable=False,
    )
    black_player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status_id: Mapped[int] = mapped_column(
        ForeignKey("pairing_statuses.id", ondelete="RESTRICT"),
        nullable=False,
    )

    tournament: Mapped[Tournament] = relationship(back_populates="pairings")
    white_player: Mapped[Player] = relationship(
        back_populates="white_pairings",
        foreign_keys=[white_player_id],
    )
    black_player: Mapped[Player] = relationship(
        back_populates="black_pairings",
        foreign_keys=[black_player_id],
    )
    status: Mapped[PairingStatus] = relationship(back_populates="pairings")

    @validates("tournament_id", "white_player_id", "black_player_id", "status_id")
    def validate_required_reference(self, key: str, value: int | None) -> int:
        if value is None:
            raise ChessTournamentValidationError(f"{key} is required")
        return value

    @validates("round_number", "board_number")
    def validate_positive_number(self, key: str, value: int) -> int:
        if value < 1:
            raise ChessTournamentValidationError(f"{key} must be greater than 0")
        return value


EXPOSED_MODELS = (Tournament, Player, Pairing, PairingStatus)
