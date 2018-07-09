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
    result = db.execute("SELECT * FROM folders WHERE user_id = :userid",
                        userid=session["user_id"])
    return result


def update_card(userid):
    result = db.execute("SELECT * FROM cards WHERE user_id = :userid",
                        userid=session["user_id"])
    return result