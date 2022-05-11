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
# os.environ.get("DATABASE_URLL")
app.config["SQLALCHEMY_DATABASE_URI"] = 'postgresql://postgres:coopgod@localhost:5432/logs'
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
    user_ID = db.Column(db.String)
    log_ID = db.Column(db.Integer)

    def __init__(self, userID, logID):
        self.user_ID = userID
        self.log_ID = logID


# Home Page
@app.route("/", methods=['GET', 'POST'])
def index():
    message = ""
    session['user'] = 'none'
    if flask.request.method == "POST":
        if request.form['button'] == 'Sign Up':
            return redirect('/signup')
        # Validate username and password, continue if successful
        else:
            username = request.values.get('formUser')
            password = request.values.get('formPass')
            validity = loginValidate(username, password)
            if validity == True:
                session['user'] = username
                return redirect("/catalog")
            else:
                # show user danger message
                message = Markup("<div class='alert alert-danger' style='margin-top: 2rem;'> \
                    Incorrect username or password. Please try again and contact \
                    the admin if the issue persists.</div> \
                    ")
                return render_template("index.html", message=message)
    else:
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
            error = Markup("<div class='alert alert-danger' style='margin-top: 2rem;'> \
                This username is already taken. Please select a different one.</div> \
                ")
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

        # if the sort by tag button is pressed
        elif buttonValue == "sort-tag":
            # gather markup and load page but SORTED BY TAG
            activeUser = session["user"]
            # if already sorted by tag, revert
            if session['sort'] == 'tag':
                session['sort'] = 'regular'
                infotable = tableMarkup(activeUser, 'regular')
                tagIcon = Markup("<i class='bi bi-dash-lg'></button></i>")
            else:
                session['sort'] = 'tag'
                infotable = tableMarkup(activeUser, 'tag')
                tagIcon = Markup("<i class='bi bi-filter'></button></i>")

            modals = modalMarkup(activeUser, False)
            dateIcon = Markup("<i class='bi bi-arrow-up'></button></i>")
            return render_template('catalog.html', infotable=infotable, modals=modals, dateIcon=dateIcon, tagIcon=tagIcon)

        # if the sort by date button is pressed
        elif buttonValue == "sort-date":
            # gather markup and load page but SORTED BY DATE
            activeUser = session["user"]
            # if already sorted by date, revert
            if session['sort'] == 'date':
                session['sort'] = 'regular'
                infotable = tableMarkup(activeUser, 'regular')
                dateIcon = Markup("<i class='bi bi-arrow-up'></button></i>")
            else:
                session['sort'] = 'date'
                infotable = tableMarkup(activeUser, 'date')
                dateIcon = Markup("<i class='bi bi-arrow-down'></button></i>")
            modals = modalMarkup(activeUser, False)
            tagIcon = Markup("<i class='bi bi-dash-lg'></button></i>")
            return render_template('catalog.html', infotable=infotable, modals=modals, dateIcon=dateIcon, tagIcon=tagIcon)

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
        session['sort'] = 'regular'
        # gather markup and load page
        activeUser = session["user"]
        infotable = tableMarkup(activeUser, 'regular')
        modals = modalMarkup(activeUser, False)
        tagIcon = Markup("<i class='bi bi-dash-lg'></button></i>")
        dateIcon = Markup("<i class='bi bi-arrow-up'></button></i>")
        return render_template('catalog.html', infotable=infotable, modals=modals, dateIcon=dateIcon, tagIcon=tagIcon)


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
        modals = modalMarkup(activeUser, True)
        return render_template('favorites.html', infotable=infotable, modals=modals)


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
def tableMarkup(user, sortBy):
    infotable = Markup("")
    # get info from favourites to then compare to ID's being added to table
    allFavorites = favorites.query.filter_by(user_ID=f"{user}")
    favoriteIDs = []
    for row in allFavorites:
        favoriteIDs.append(row.log_ID)
    # order by chosen value
    if sortBy == 'regular':
        userWritings = writings.query.order_by(
            desc(writings.ID)).filter_by(user_ID=f"{user}")
    elif sortBy == 'tag':
        userWritings = writings.query.order_by(
            writings.tag).filter_by(user_ID=f"{user}")
    else:
        userWritings = writings.query.order_by(
            writings.ID).filter_by(user_ID=f"{user}")
    # create table to add to HTML
    for row in userWritings:
        # colour for favorite indication
        favoriteClass = 'btn-light'
        if row.ID in favoriteIDs:
            favoriteClass = 'btn-warning'
        # create markup for html injection
        infotable = infotable + Markup(f"<tr><td><button type='button' class='btn btn-primary'  \
                data-toggle='modal' data-target='#{row.ID}Modal'>View</button></td> \
            <td>{row.passage}</td> \
            <td>{row.tag}</td> \
            <td>{row.date}</td> \
            <td><button class='btn {favoriteClass}' name='button' value='f{row.ID}'>Favorite</button></td> \
            <td><button class='btn btn-danger' name='button' value='d{row.ID}'>Delete</button></td></tr>")
    return infotable


# function to create modal for each data entry to add to html via jijna
def modalMarkup(user, isFavorite):
    modals = Markup("")
    if isFavorite == True:
        # get info from favourites to then compare to ID's being added to table
        allFavorites = favorites.query.filter_by(user_ID=session['user'])
        favoriteIDs = []
        for row in allFavorites:
            favoriteIDs.append(row.log_ID)
        userWritings = writings.query.order_by(
            desc(writings.ID)).filter_by(user_ID=f"{user}")
    else:
        userWritings = writings.query.order_by(
            desc(writings.ID)).filter_by(user_ID=f"{user}")
    for row in userWritings:
        # create modal
        modals += Markup(f'<div class="modal fade" id="{row.ID}Modal" tabindex="-1" role="dialog" \
                aria-labelledby="{row.ID}ModalLabel" aria-hidden="true">\
            <div class="modal-dialog" role="document">\
                <div class="modal-content">\
                <div class="modal-header">\
                    <h5 class="modal-title" id="{row.ID}ModalLabel">Gr8fulness Log</h5>\
                    <button type="button" class="close" data-d\miss="modal" aria-label="Close">\
                    <span aria-hidden="true">&times;</span> \
                    </button>\
                </div>\
                <div class="modal-body">\
                    <ul> \
                        <li>{row.grateful1}</li> \
                        <li>{row.grateful2}</li> \
                        <li>{row.grateful3}</li> \
                    </ul>\
                </div>\
                <div class="modal-footer">\
                    <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>\
                </div>\
                </div>\
            </div>\
            </div>')
    return modals

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
            infotable = infotable + Markup(f"<tr><td><button type='button' class='btn btn-primary'  \
                    data-toggle='modal' data-target='#{row.ID}Modal'>View</button></td> \
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
    # null handler cause nothing looks dumb
    if g1 == "":
        g1 = "Something cool, I'm sure"
    if g2 == "":
        g2 = "Something cool, I'm sure"
    if g3 == "":
        g3 = "Something cool, I'm sure"
    if passage == "":
        passage = "None Today"
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
