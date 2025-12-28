from __future__ import annotations  #後のバージョンのPythonの機能を先取りして使うための記述 

import os
from typing import Callable   #型ヒントのモジュール

# 各ページをフォルダからインポート
from pages import (
    AdminGateCheck,
    AdminMenu,
    AdminMovieDelete,
    AdminMovieEdit,
    AdminMovieList,
    AdminScheduleEdit,
    UserCheckout,
    UserCancelTicket,
    UserReservationList,
    UserMenu,
    UserMovieBrowse,
    UserShowCalendar,
    UserSeatSelect,
    UserShowSelect,
    UserTicketQR,
    login,
)

Session = dict

#Callableは型ヒントの一環。PageFnがSessionを引数に取り、更新後のSessionを返す関数であることを示す。
PageFn = Callable[[Session], Session]

# コマンドラインのクリア
def _clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def _resolve_next_page(current: str, session: Session, result: Session) -> tuple[str | None, Session]:

    # ページから返ってきたSessionでセッションを更新
    if isinstance(result, dict):
        session = result

    # ↑ページごとの差異を吸収する処理。

    next_page = session.pop("next_page", None)
    if next_page is not None:
        return next_page, session

    # ログインページからの遷移の場合
    if current == "login":
        role = session.get("user_role")

        # 対応するメニュー画面へ振り分け、なければ終了
        if role == "Admin": 
            return "admin_menu", session
        if role == "User":
            return "user_menu", session
        return "exit", session

    # If a page doesn't specify a next page yet, stop instead of looping forever.
    return None, session

# メインルーター関数
def run_router() -> None:
    pages: dict[str, PageFn] = {
        "login": login.run,
        "admin_menu": AdminMenu.run,
        "admin_movie_list": AdminMovieList.run,
        "admin_movie_edit": AdminMovieEdit.run,
        "admin_movie_delete": AdminMovieDelete.run,
        "admin_schedule_edit": AdminScheduleEdit.run,
        "admin_gate_check": AdminGateCheck.run,
        "user_menu": UserMenu.run,
        "user_movie_browse": UserMovieBrowse.run,
        "user_show_calendar": UserShowCalendar.run,
        "user_show_select": UserShowSelect.run,
        "user_seat_select": UserSeatSelect.run,
        "user_checkout": UserCheckout.run,
        "user_ticket_qr": UserTicketQR.run,
        "user_cancel_ticket": UserCancelTicket.run,
        "user_reservation_list": UserReservationList.run,
        "exit": lambda s: ("exit", s),
    }

    # 初回起動でloginに飛ばす
    session: Session = {"current_page": "login"}
    current = session["current_page"]

    # メインループ、while trueで遷移を待ち受けて都度動く
    while True:
        page_fn = pages.get(current)    # 現在のページ名から関数を取得
        if page_fn is None:
            _clear_screen()
            print(f"Unknown page: {current}")
            break

        _clear_screen()
        result = page_fn(session)   # 上で取得した関数を実行、ページ遷移して結果を受け取る
        next_page, session = _resolve_next_page(current, session, result)   # resultをもとに次のページを探す

        if next_page is None or next_page == "exit":
            break
        
        # セッション更新
        current = next_page
        session["current_page"] = current

        #　あとはwhileのトップに戻ってもう一度今の流れを繰り返す


# エントリーポイント
if __name__ == "__main__":
    run_router()