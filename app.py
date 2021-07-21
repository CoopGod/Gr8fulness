# imports ------ python -m flask run
from datetime import datetime
from logging import info
from os import access
import flask
from datetime import date
from flask import Flask, render_template, Markup, request, session
from flask.helpers import total_seconds
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from sqlalchemy.orm import query
from sqlalchemy.sql.elements import Null
from werkzeug.utils import redirect

# flask and postgres setup
app = Flask(__name__)
app.secret_key = "oh_so_secret"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = 'postgres://wkplzdpcuvcdbp:a26cdeabd8551f1578d9be0e151c1afb88f469f315bf90bf5232073c49bdddcf@ec2-52-72-125-94.compute-1.amazonaws.com:5432/dfpu28ru0s3ujl'
db = SQLAlchemy(app)

#class defining user writings/entries 
class writings(db.Model):
    ID = db.Column(db.Integer, primary_key=True, nullable=False)
    index = db.Column(db.String)
    date = db.Column(db.Date)
    user = db.Column(db.String)

    def __init__(self, index, date, user):
        self.index = index
        self.date = date
        self.user = user

# class defining the user for login purposes
class users(db.Model):
    ID = db.Column(db.Integer, primary_key=True, nullable=False)
    username = db.Column(db.String)
    password = db.Column(db.String)

    def __init__(self, username, password):
        self.username = username
        self.password = password

    
# Home Page
@app.route("/", methods=['GET','POST'])
def index():
    # Validate username and password, continue if successful
    if flask.request.method == "POST":
        username = request.values.get('formUser')
        password = request.values.get('formPass')
        validity = loginValidate(username, password)
        print(validity)
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


# Catalog page. See all your entries.
@app.route("/catalog", methods=['GET','POST'])
def catalog():
    if flask.request.method == "POST":
        return redirect('/new-entry')
    else:
        # table markup function
        activeUser = session["user"]
        infotable = tableMarkup(activeUser)
        return render_template('catalog.html', infotable=infotable)

# page to add entries
@app.route("/new-entry", methods=["GET","POST"])
def newEntry():
    if flask.request.method == "POST":
        entry = request.values.get('formSubmission')
        logWriting(entry)
        return redirect('/catalog')
    else:
        return render_template('add.html')

# Helper functions --------------------------------------------------------------------------------------------------------------
# function to create table markup for catalog page
def tableMarkup(user):
    userWritings = writings.query.order_by(desc(writings.ID)).filter_by(user = f"{user}")
    infotable = Markup("")
    for row in userWritings:
        infotable = infotable + Markup(f"<tr class='tbl-content'><th>{row.index}</th><th>{row.date}</th></tr>")
    return infotable

# function to check username and password combinations. returns true if user is valid
def loginValidate(usernameVal, passwordVal):
    allUsers = users.query.filter_by(username = usernameVal)
    for row in allUsers:
        if row.password == passwordVal:
            return True
    return False

#funciton to create and submit row for SQL
def logWriting(submission):
    todaysDate = date.today()
    new_writing = writings(submission, todaysDate, session['user'])
    db.session.add(new_writing)
    db.session.commit()
    

# Run flask app --------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
