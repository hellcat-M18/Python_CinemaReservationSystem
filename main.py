import rich
import pandas as pd
import pydantic

from pages import login

def main():

    session = {}

    session = login.run(session)

    if(session["userRole"] == "Admin"):

        rich.print("wip")

    else:

        rich.print("wip")


main()