import os
import requests
import sqlite3
import urllib.parse
from werkzeug.security import check_password_hash, generate_password_hash

from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session

app = Flask(__name__)

#Configure session to use filesystem instead of signed cookies
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#Create data global. It will be updated whenever a search is made. 
#This prevents it being called when item or other pages are loaded, but means we must perform a search on server bootup
data = {}

#Change the user agent for python requests
headers = {
    'User-Agent': 'Test Project - irish775#2989',
}
    

@app.route("/")
def home():
    #This gets the data for the abyssal whip and renders the search page
    if list(session.keys())[0] == "user_id":
        return render_template("search.html")
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        db = sqlite3.connect("main.db")
        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("noUser.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("noPass.html")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", (request.form.get("username"),)).fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0][2], request.form.get("password")):
            return render_template("incorrectLogin.html")

        # Remember which user has logged in
        session["user_id"] = rows[0][0]

        db.close()

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    # Forget any user_id
    session.clear()

    # Redirect user to home page
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    session.clear()

    """Register user"""
    #If the request method is get, render a form to allow them to input info
    #The form should post that info back to /register
    if request.method == "GET":
        return render_template("register.html")

    #Validate the response server-side before storing at as a new user in finance.db
    if request.method=="POST":
        db = sqlite3.connect("main.db")
        #Make sure the username exists
        if not request.form.get("username"):
            return render_template("registrationFailed.html", error="Please enter a username.")

        #Make sure it is not already registered
        for row in db.execute("SELECT * FROM users WHERE username = ?", (request.form.get("username"),)):
            return render_template("registrationFailed.html", error="Username already in use.")

        #Make sure neither password is blank
        if not request.form.get("password"):
            return render_template("registrationFailed.html", error="Please enter a password.")
        if not request.form.get("confirmation"):
            return render_template("registrationFailed.html", error="Must confirm password.")

        #Make sure the passwords match
        if request.form.get("password") != request.form.get("confirmation"):
            return render_template("registrationFailed.html", error="Password and confirmation must match.")

        #Store the new user
        username = request.form.get("username")
        hash = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", (username, hash,))
        db.commit()
        db.close()
        
        #After storing the new user, render registered template which extends /login with a success message
        return render_template("registered.html")

@app.route("/search")
def search():

    if not request.args.get("value"):
        #Make a search bar with a submit button
        return render_template("search.html")
    
    #Fetch data from the API and convert to json
    url = f"https://prices.runescape.wiki/api/v1/osrs/latest"
    response = requests.get(url=url,headers=headers)
    response = response.json()

     #Save the data as a dictionary
    data.update(response["data"])
    #Check if item name or id was entered
    #Find the latest prices of the item
    #Display the name,  id and prices
    search = request.args.get("value")
    ids = []
    names = []
    highPrices=[]
    lowPrices=[]
    buyLimits = []
    db = sqlite3.connect("main.db")
    #If the search term is an integer, search for the name based on the id
    length = False
    try:
        id = int(search)
        ids.append(id)
        cur = db.cursor()
        rows = cur.execute("SELECT * FROM items WHERE id = ?;", (id,))

        #This moves through the result from the select and adds the id, name, and prices to the respective lists
        for row in rows:
            length = True
            name = row[1]
            print(name)
            names.append(name.title())
            buyLimits.append(row[2])
            prices = data[f"{id}"]
            highPrices.append(prices['high'])
            lowPrices.append(prices['low'])
    
    #If the search is not an integer, search for the id, name and prices based on the search term in the sql database
    except ValueError:
        cur = db.cursor()
        
        #This moves through each result from the select and adds the id, name, and prices to the respective lists
        for row in cur.execute("SELECT * FROM items WHERE name LIKE ?;", ("%"+search+"%",)):
            length = True
            try:
                prices = data[f"{row[0]}"]
            except KeyError:
                continue
            ids.append(row[0])
            names.append(row[1].title())
            buyLimits.append(row[2])
            highPrices.append(prices['high'])
            lowPrices.append(prices['low'])
    db.close()
    
    if not length:
        return render_template("itemMissing.html", search=search)

    return render_template("searched.html", ids=ids,names=names, highPrices=highPrices, 
    lowPrices=lowPrices, buyLimits=buyLimits, search=search)

@app.route("/item")
def item():
    
    #Return an error if there is no item id entered
    if not request.args.get("id"):
        return render_template("404error.html", error="Item does not exist.")

    #Render information based on the item id entered
    #Get the id
    id = request.args.get("id")

    highPrice = data[str(id)]["high"]
    lowPrice = data[str(id)]["low"]

    #Get the item name based on id
    name = "NULL"
    db = sqlite3.connect("main.db")
    cur = db.cursor()
    rows = cur.execute("SELECT * FROM items WHERE id = ?;", (id,))
    for row in rows:
        name = row[1].title()
        buyLimit = row[2]
        description = row[3]
    db.close()
    #Render error if name not found
    if name == "NULL":
        return render_template("404error.html", error="Item not found.")
    
    #Render the item's page
    return render_template("item.html", name=name, description=description, id=id, highPrice=highPrice, lowPrice=lowPrice, buyLimit=buyLimit)
