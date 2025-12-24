from __future__ import annotations

from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    duration_min: Mapped[int] = mapped_column(Integer, nullable=False)

    # JSON文字列を入れる想定（例: '["action","comedy"]'）
    tags_json: Mapped[str] = mapped_column(String, nullable=False, default="[]")

    # 作品説明（任意）
    description: Mapped[str | None] = mapped_column(String, nullable=True)

    run_start_date: Mapped[str | None] = mapped_column(String, nullable=True)  # YYYY-MM-DD
    run_end_date: Mapped[str | None] = mapped_column(String, nullable=True)    # YYYY-MM-DD

    shows: Mapped[list["Show"]] = relationship(back_populates="movie")


class Show(Base):
    __tablename__ = "shows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), nullable=False)

    hall: Mapped[str] = mapped_column(String, nullable=False)      # "A"～"D"
    start_at: Mapped[str] = mapped_column(String, nullable=False)  # 文字列でOK（ISO8601推奨）
    price: Mapped[int] = mapped_column(Integer, nullable=False)

    movie: Mapped["Movie"] = relationship(back_populates="shows")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="show")


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # QRに入れる一意ID
    uuid: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    show_id: Mapped[int] = mapped_column(ForeignKey("shows.id"), nullable=False)

    # user info（必要なものだけ）
    user_name: Mapped[str | None] = mapped_column(String, nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sex: Mapped[str | None] = mapped_column(String, nullable=True)
    is_member: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 0/1

    # 内訳をJSON文字列で保持（例: '{"adult":1,"child":1}'）
    breakdown_json: Mapped[str] = mapped_column(String, nullable=False, default="{}")

    sum_price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # 改札用に最低限（使う/使わないは後で決めてOK）
    issued_at: Mapped[str | None] = mapped_column(String, nullable=True)
    used_at: Mapped[str | None] = mapped_column(String, nullable=True)

    show: Mapped["Show"] = relationship(back_populates="tickets")

    seats: Mapped[list["TicketSeat"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
    )


class TicketSeat(Base):
    __tablename__ = "ticket_seats"
    __table_args__ = (
        # 同一showで同一seatを二重予約できないようにする
        UniqueConstraint("show_id", "seat", name="uq_ticket_seats_show_seat"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), nullable=False)
    show_id: Mapped[int] = mapped_column(ForeignKey("shows.id"), nullable=False)

    seat: Mapped[str] = mapped_column(String, nullable=False)  # "A-1" 等

    ticket: Mapped["Ticket"] = relationship(back_populates="seats")