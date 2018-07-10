import os

from flask import redirect, render_template, request, session
from functools import wraps

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

from cs50 import SQL
db = SQL("sqlite:///flashcard.db")


def countcard(folderid):
    result = db.execute("SELECT COUNT (id) FROM cards WHERE folder_id = :folderid",
                           folderid=folderid)
    return result


def update_folder(userid):
#    result = db.execute("SELECT * FROM folders WHERE user_id = :userid",
#                        userid=session["user_id"])

    result = db.execute("""SELECT folders.id id, folders.name name, COUNT(cards.id) card_amount
                        FROM folders INNER JOIN users ON folders.user_id=users.id
                        LEFT JOIN cards ON folders.id=cards.folder_id
                        WHERE folders.user_id = :userid
                        GROUP BY folders.id""",
                        userid=userid)
    return result


def update_card(folderid):
#    result = db.execute("SELECT * FROM cards WHERE user_id = :userid",
#                        userid=session["user_id"])

    result = db.execute("SELECT * FROM cards WHERE folder_id = :folderid",
                         folderid=folderid)
    return result


def show_card(folderid):
    result = db.execute("SELECT id, front, back FROM cards WHERE folder_id = :folderid",
                        folderid=folderid)

    return result