import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp

from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, update_folder, update_card, countcard

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///flashcard.db")


@app.route("/")
def index():

    # Redirect to dashboard if user has login
    if session.get("user_id") is None:
        return render_template("index.html")
    else:
        return redirect(url_for('dashboard'))


@app.route("/dashboard")
@login_required
def dashboard():
    userid = session["user_id"]

    folders = update_folder(userid)
    active_folder = folders[0]["id"]

    cards = update_card(active_folder)

    session["folders"] = folders
    session["cards"] = cards

    # Set default folder to show on view
    active_folder = folders[0]["id"]


    return render_template("index.html", folders=folders, cards=cards)


@app.route("/login", methods=["GET", "POST"])
def login():

    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("Invalid username or password")
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        userid = session["user_id"]

        # Update session
        folders = update_folder(userid)
        cards = update_card(userid)

        session["folders"] = folders
        session["cards"] = cards

        # Redirect user to home page
        return redirect(url_for('dashboard'))

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Query database for username and render apology if username already exist
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        if len(rows) >= 1:
            flash("Username already exists, try another")
            return render_template("register.html")

        # if username not found, insert to database
        else:
            user = db.execute("INSERT INTO users (username, hash) VALUES (:user, :hashed_pass)",
                              user=request.form.get("username"), hashed_pass=generate_password_hash(request.form.get("password")))

            session["user_id"] = user
            userid = session["user_id"]

            # Make default folder
            folderid = db.execute("INSERT INTO folders (name, user_id) VALUES (:name, :userid)",
                                  name="My folder", userid=userid)

            # Make first card
            db.execute("INSERT INTO cards (folder_id, user_id, front, back) VALUES (:folderid, :userid, :front, :back)",
                       folderid=folderid, userid=userid, front="Front text here", back="Back text goes here")

            # Update session
            folders = update_folder(userid)
            cards = update_card(userid)

            session["folders"] = folders
            session["cards"] = cards

            # Redirect user to dashboard
            flash("You're registered :) Start building your flashcards!")

            return redirect(url_for('dashboard'))


    # User reached route via GET (as by clicking a link or via redirect)
    else:
        # Forget any user_id
        session.clear()
        return render_template("register.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to home
    return redirect("/")


@app.route("/newfolder", methods=["POST"])
@login_required
def newfolder():
    """Create new folders"""

    userid = session["user_id"]
    foldername = request.form.get("foldername")

    # Avoid same folder name
    rows = db.execute("SELECT * FROM folders WHERE user_id = :userid AND name = :foldername",
                     userid=userid, foldername=foldername)

    if len(rows) >= 1:

        folders = update_folder(userid)
        cards = update_card(userid)

        session["folders"] = folders
        session["cards"] = cards


        flash("Folder name already exists")
        return redirect(url_for('dashboard'))

    else:
        # Check amount of folders
        folders = update_folder(userid)

        # Failed to create new folder if user already have 5 folders
        if len(folders) >= 5:
            cards = update_card(userid)

            session["folders"] = folders
            session["cards"] = cards

            # Redirect user to home page
            flash("Maximum folders you can have is 5 folders")
            return redirect(url_for('dashboard'))

        else:
            db.execute("INSERT INTO folders (name, user_id) VALUES (:name, :userid)",
                       name=foldername, userid=userid)

            folders = update_folder(userid)
            cards = update_card(userid)

            session["folders"] = folders
            session["cards"] = cards

            # Redirect user to home page
            return redirect(url_for('dashboard'))


@app.route("/newcard", methods=["POST"])
@login_required
def newcard():
    """Create new cards"""

    userid=session["user_id"]

    # Get folder id
    foldername = request.form.get("foldername")

    row = db.execute("SELECT id FROM folders WHERE user_id = :userid AND name = :foldername",
                          userid=userid, foldername=foldername)
    folderid = row[0]["id"]

    # Insert new card to database
    db.execute("INSERT INTO cards (folder_id, user_id, front, back) VALUES (:folderid , :userid, :front, :back)",
               folderid=folderid, userid=userid, front=request.form.get("front"), back=request.form.get("back"))

    # Update session
    folders = update_folder(userid)
    cards = update_card(userid)

    session["folders"] = folders
    session["cards"] = cards

    # Redirect user to home page
    return redirect(url_for('dashboard'))


@app.route("/editfolder", methods=["POST"])
@login_required
def editfolder():
    """Edit selected folder"""

    # Get folder id
    folderid = request.form.get("folderid")
    userid = session["user_id"]

    if request.form.get("action") == "rename":
        # Rename folder
        newname = request.form.get("newname")

        db.execute("UPDATE folders SET name = :newname WHERE id = :folderid",
                    newname=newname, folderid=folderid)

    if request.form.get("action") == "delete":
        # DELETE FOLDER
        userid=session["user_id"]

        # Don't execute if it's the last folder
        folders = update_folder(userid)
        if len(folders) <= 1:
            flash("You cannot delete your last folder")

            # Redirect user to home page
            return redirect(url_for('dashboard'))

        else:
            # Delete folder
            db.execute("DELETE FROM folders WHERE user_id = :userid AND id = :folderid",
                       userid=userid, folderid=folderid)

            # Delete all cards within folder
            db.execute("DELETE FROM cards WHERE folder_id = :folderid",
                       folderid=folderid)

    # Update session
    folders = update_folder(userid)
    cards = update_card(userid)

    session["folders"] = folders
    session["cards"] = cards

    # Redirect user to home page
    return redirect(url_for('dashboard'))


@app.route("/editcard", methods=["POST"])
@login_required
def editcard():
    """Edit selected card"""

    userid=session["user_id"]

    # Get card id
    card_id=request.form.get("card_id")

    if request.form.get("action") == "edit":
        front = request.form.get("newfront")
        back = request.form.get("newback")

        # Edit card content
        db.execute("UPDATE cards SET front = :front, back = :back WHERE id = :card_id",
                    front=front, back=back, card_id=card_id)

    if request.form.get("action") == "delete":
        # Delete card
        db.execute("DELETE FROM cards WHERE user_id = :userid AND id = :card_id",
                   userid=userid, card_id=card_id)

    # Update session
    folders = update_folder(userid)
    cards = update_card(userid)

    session["folders"] = folders
    session["cards"] = cards

    # Redirect user to home page
    return redirect(url_for('dashboard'))