import os
import rich
from rich.console import Console

console = Console()

def run(session: dict) -> dict:

    os.system("cls")

    userName, passWord = "", ""

    userName = input("Enter your name: ")

    if userName == "root":

        passWord = input("Enter your password: ")
        if passWord == "password123":
            console.print("Access Granted!")

            session["userRole"] = "Admin"

            return session
        
        else:

            session = run(session)

            return session
    else:

        console.print(f"Welcome, [#00ff00]{userName}[/]!")

        session["userRole"] = "User"

        return session
# run({})