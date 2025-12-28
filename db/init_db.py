from db import reset_db

if __name__ == "__main__":
    reset_db(remove_file=True)
    print("OK: reset tables in cinema.db")