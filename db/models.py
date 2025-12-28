from __future__ import annotations

import uuid

from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


#DBのテーブル定義


class User(Base):
    __tablename__ = "users"

    # UUID文字列を主キーにする（作り直し前提なのでマイグレーション不要）
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # ログインID（ユニーク）
    username: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    # passlib等で生成したハッシュを保存
    password_hash: Mapped[str] = mapped_column(String, nullable=False)

    # "Admin" / "User"
    role: Mapped[str] = mapped_column(String, nullable=False, default="User")

    created_at: Mapped[str | None] = mapped_column(String, nullable=True)

    # Ticketとの関連
    tickets: Mapped[list["Ticket"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

class Movie(Base):
    __tablename__ = "movies"

    #基本情報
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    duration_min: Mapped[int] = mapped_column(Integer, nullable=False)

    # 映画ごとの基本料金（Show生成時の初期値として使う想定）
    default_price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # JSON文字列を入れる想定（例: '["action","comedy"]'）
    tags_json: Mapped[str] = mapped_column(String, nullable=False, default="[]")

    # 作品説明（任意）
    description: Mapped[str | None] = mapped_column(String, nullable=True)

    # 上映期間（任意）
    run_start_date: Mapped[str | None] = mapped_column(String, nullable=True)  # ISO8601 
    run_end_date: Mapped[str | None] = mapped_column(String, nullable=True)    # ISO8601

    # Showとの関連付け
    shows: Mapped[list["Show"]] = relationship(
        back_populates="movie",
        cascade="all, delete-orphan",
    )


class Show(Base):
    __tablename__ = "shows"

    #回ごとのidと、上映される映画のID
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), nullable=False)

    # 上映情報
    hall: Mapped[str] = mapped_column(String, nullable=False)      # "A"～"D"
    start_at: Mapped[str] = mapped_column(String, nullable=False)  # ISO8601
    end_at: Mapped[str] = mapped_column(String, nullable=False)    # ISO8601
    #end_atはmovieのduration_minから自動算出(持っとく方が便利)

    # 価格情報（基本料金）
    price: Mapped[int] = mapped_column(Integer, nullable=False)

    # Movieとの関連付け
    movie: Mapped["Movie"] = relationship(back_populates="shows")

    # ticketとの関連付け + showが消えると自動で対応するticketも消える 
    tickets: Mapped[list["Ticket"]] = relationship(
        back_populates="show",
        cascade="all, delete-orphan",
    )


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # QRに入れる一意ID、当日改札の照合用
    uuid: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    show_id: Mapped[int] = mapped_column(ForeignKey("shows.id"), nullable=False)

    # 誰のチケットか（認証導入に伴い必須）
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)

    # user info（必要なものだけ）
    user_name: Mapped[str | None] = mapped_column(String, nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sex: Mapped[str | None] = mapped_column(String, nullable=True)
    is_member: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 0/1

    # 人員内訳をJSON文字列で保持（例: '{"adult":1,"child":1}'）
    breakdown_json: Mapped[str] = mapped_column(String, nullable=False, default="{}")

    sum_price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # 改札用に、発行・使用日時を保持
    issued_at: Mapped[str | None] = mapped_column(String, nullable=True)
    used_at: Mapped[str | None] = mapped_column(String, nullable=True)

    # Showとの関連付け
    show: Mapped["Show"] = relationship(back_populates="tickets")

    # Userとの関連付け
    user: Mapped["User"] = relationship(back_populates="tickets")

    # TicketSeatとの関連付け + ticketが消えると自動で対応するticket_seatも消える
    seats: Mapped[list["TicketSeat"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
    )

# 予約された座席情報
# 同一showで同一seatを二重予約できないように設定
class TicketSeat(Base):
    __tablename__ = "ticket_seats"
    __table_args__ = (
        # 同一showで同一seatを二重予約できないようにする
        UniqueConstraint("show_id", "seat", name="uq_ticket_seats_show_seat"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 親子関係の定義
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), nullable=False)
    show_id: Mapped[int] = mapped_column(ForeignKey("shows.id"), nullable=False)

    # 
    seat: Mapped[str] = mapped_column(String, nullable=False)  # "A-1" 等

    ticket: Mapped["Ticket"] = relationship(back_populates="seats")