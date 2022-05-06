# imports ------ python -m flask run
import os
import flask
from datetime import date
from flask import Flask, render_template, Markup, request, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from werkzeug.utils import redirect

# flask and postgres setup
app = Flask(__name__)
app.secret_key = "oh_so_secret"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URLL") #'postgresql://postgres:coopgod@localhost:5432/logs' 
db = SQLAlchemy(app)

# class defining user writings/entries


class writings(db.Model):
    ID = db.Column(db.Integer, primary_key=True, nullable=False)
    date = db.Column(db.Date)
    grateful1 = db.Column(db.String)
    grateful2 = db.Column(db.String)
    grateful3 = db.Column(db.String)
    passage = db.Column(db.String)
    tag = db.Column(db.String)
    user_ID = db.Column(db.Integer)

    def __init__(self, date, g1, g2, g3, passage, tag, userID):
        self.date = date
        self.grateful1 = g1
        self.grateful2 = g2
        self.grateful3 = g3
        self.passage = passage
        self.tag = tag
        self.user_ID = userID

# class defining the user for login purposes


class users(db.Model):
    ID = db.Column(db.Integer, primary_key=True, nullable=False)
    username = db.Column(db.String)
    password = db.Column(db.String)

    def __init__(self, username, password):
        self.username = username
        self.password = password

# class defining users favorite entries


class favorites(db.Model):
    ID = db.Column(db.Integer, primary_key=True, nullable=False)
    user_ID = db.Column(db.Integer)
    log_ID = db.Column(db.Integer)

    def __init__(self, userID, logID):
        self.user_ID = userID
        self.log_ID = logID


# Home Page
@app.route("/", methods=['GET', 'POST'])
def index():
    # Validate username and password, continue if successful
    if flask.request.method == "POST":
        if request.form['button'] == 'signup':
            return redirect('/signup')
        else:
            username = request.values.get('formUser')
            password = request.values.get('formPass')
            validity = loginValidate(username, password)
            if validity == True:
                session['user'] = username
                return redirect("/catalog")
            else:
                message = "Incorrect Username or Password!"
                return render_template("index.html", message=message)
    else:
        message = ""
        session['user'] = 'none'
        return render_template("index.html", message=message)


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    error = ""
    if flask.request.method == "POST":
        username = request.values.get('formUser')
        password = request.values.get("formPass")
        new_user = makeUser(username, password)
        if new_user != False:
            session['user'] = username
            return redirect("/catalog")
        else:
            error = "Username Already Taken!"
            return render_template("signup.html", error=error)

    else:
        return render_template("signup.html", error=error)


# Catalog page. See all your entries.
@app.route("/catalog", methods=['GET', 'POST'])
def catalog():
    if flask.request.method == "POST":
        buttonValue = request.form['button']
        # if the new entry button is pressed
        if buttonValue == 'New Entry':
            return redirect('/newEntry')
        # if the favorites button is pressed
        elif buttonValue == "Favorites":
            return redirect('/favorites')
        elif buttonValue == "Catalog":
            return redirect('/catalog')
        # if one of the favorite buttons is pressed
        else:
            entryID = int(buttonValue[1:])
            entryFunction = buttonValue[0]
            # if a favorite button was pressed:
            if entryFunction == 'f':
                # check if is favorited. yes: remove. no: add
                favoritesCount = favorites.query.filter_by(
                    log_ID=entryID).count()
                if favoritesCount > 0:
                    deleteFavourite(entryID)
                    return redirect('/catalog')
                else:
                    addFavourite(entryID, session['user'])
                    return redirect('catalog')
            # if delete button was pressed
            else:
                deleteWriting(entryID)
                return redirect('/catalog')
    else:
        # table markup function
        activeUser = session["user"]
        infotable = tableMarkup(activeUser)
        return render_template('catalog.html', infotable=infotable)


# page to view saved favorites
@app.route("/favorites", methods=["GET", "POST"])
def favoritesPage():
    if flask.request.method == "POST":
        buttonValue = request.form['button']
        # if the new entry button is pressed
        if buttonValue == 'New Entry':
            return redirect('/newEntry')
        # if the favorites button is pressed
        elif buttonValue == "Favorites":
            return redirect('/favorites')
        elif buttonValue == "Catalog":
            return redirect('/catalog')
    else:
        activeUser = session["user"]
        infotable = favoriteMarkup(activeUser)
        return render_template('favorites.html', infotable=infotable)


# page to add entries
@app.route("/newEntry", methods=["GET", "POST"])
def newEntry():
    if flask.request.method == "POST":
        buttonValue = request.form['button']
        # if the new entry button is pressed
        if buttonValue == 'New Entry':
            return redirect('/newEntry')
        # if the favorites button is pressed
        elif buttonValue == "Favorites":
            return redirect('/favorites')
        elif buttonValue == "Catalog":
            return redirect('/catalog')
        else:
            # get all values from form and add them to new writing
            g1 = request.values.get('g1')
            g2 = request.values.get('g2')
            g3 = request.values.get('g3')
            passage = request.values.get('passage')
            tag = request.values.get('tags')
            logWriting(g1, g2, g3, passage, tag)
        return redirect('/catalog')
    else:
        return render_template('add.html')


# Helper functions --------------------------------------------------------------------------------------------------------------
# function to create table markup for catalog page
def tableMarkup(user):
    infotable = Markup("")
    # get info from favourites to then compare to ID's being added to table
    allFavorites = favorites.query.filter_by(user_ID=session['user'])
    favoriteIDs = []
    for row in allFavorites:
        favoriteIDs.append(row.log_ID)
    # create table to add to HTML
    userWritings = writings.query.order_by(
        desc(writings.ID)).filter_by(user_ID=f"{user}")
    for row in userWritings:
        # colour for favorite indication
        favoriteClass = 'btn-light'
        if row.ID in favoriteIDs:
            favoriteClass = 'btn-warning'
        # create markup for html injection
        infotable = infotable + Markup(f"<tr><td>{row.grateful1}</td> \
            <td>{row.grateful2}</td> \
            <td>{row.grateful3}</td> \
            <td>{row.passage}</td> \
            <td>{row.tag}</td> \
            <td>{row.date}</td> \
            <td><button class='btn {favoriteClass}' name='button' value='f{row.ID}''>Favorite</button></td> \
            <td><button class='btn btn-danger' name='button' value='d{row.ID}'>Delete</button></td></tr>")
    return infotable


# function to create table markup for favorites page
def favoriteMarkup(user):
    infotable = Markup("")
    # get info from favourites to then compare to ID's being added to table
    allFavorites = favorites.query.filter_by(user_ID=session['user'])
    favoriteIDs = []
    for row in allFavorites:
        favoriteIDs.append(row.log_ID)
    # create table to add to HTML
    userWritings = writings.query.order_by(
        desc(writings.ID)).filter_by(user_ID=f"{user}")
    for row in userWritings:
        # colour for favorite indication
        if row.ID in favoriteIDs:
            # create markup for html injection
            infotable = infotable + Markup(f"<tr><td>{row.grateful1}</td> \
                <td>{row.grateful2}</td> \
                <td>{row.grateful3}</td> \
                <td>{row.passage}</td> \
                <td>{row.tag}</td> \
                <td>{row.date}</td></tr>")
    return infotable

# function to check username and password combinations. returns true if user is valid


def loginValidate(usernameVal, passwordVal):
    allUsers = users.query.filter_by(username=usernameVal)
    for row in allUsers:
        if row.password == passwordVal:
            return True
    return False


# function to check if username is already taken and if not, add it
def makeUser(usernameVal, passwordVal):
    allUsers = users.query.filter_by(username=usernameVal)
    userCount = allUsers.count()
    if userCount > 0:
        return False
    else:
        new_user = users(usernameVal, passwordVal)
        db.session.add(new_user)
        db.session.commit()


# funciton to create and submit row for SQL
def logWriting(g1, g2, g3, passage, tag):
    todaysDate = date.today()
    new_writing = writings(todaysDate, g1, g2, g3,
                           passage, tag, session['user'])
    db.session.add(new_writing)
    db.session.commit()


# function to delete log
def deleteWriting(logID):
    writings.query.filter_by(ID=logID).delete()
    db.session.commit()


# function to add favourite to list
def addFavourite(logID, userID):
    new_favourite = favorites(userID, logID)
    db.session.add(new_favourite)
    db.session.commit()


def deleteFavourite(logID):
    favorites.query.filter_by(log_ID=logID).delete()
    db.session.commit()


# Run flask app --------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
