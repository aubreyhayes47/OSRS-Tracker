import os
from re import L
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
        #Get all holdings of user
        holdings = []
        db = sqlite3.connect("main.db")
        rows = db.execute("SELECT item_id FROM holdings WHERE user_id = ?;", (session["user_id"],))
        #Make a dict for each item that is held. The first key of the dict is the item id 
        for row in rows:
            #Find the item name and info
            #For name and buy limit, we must call the item db, which returns a set. Sets don't support indexing so 
            #we cast it to a list and index in
            name = list(db.execute("SELECT name FROM items WHERE id = ?", (row[0],)).fetchall()[0])[0]
            buyLimit = list(db.execute("SELECT buyLimit FROM items WHERE id = ?", (row[0],)).fetchall()[0])[0]
            #For prices, we index into data which is updated whenever a search is performed
            prices = data[f"{row[0]}"]
            highPrice = prices["high"]
            lowPrice = prices["low"]
            #Finally, holdings is a list of dicts
            #Each dict has info for the item that is held
            holdings.append({"id":row[0],"name":name, "highPrice":highPrice,"lowPrice":lowPrice,"buyLimit":buyLimit,})
        db.close()
        #Load up their portfolio
        holdings = sorted(holdings, key=lambda i:i["name"])
        return render_template("portfolio.html", holdings=holdings)
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

        #Disallow forbidden characters in password
        forbiddenChars = [",",";","'","\"",":"]
        for char in forbiddenChars:
            if char in request.form.get("password") or request.form.get("username"):
                return render_template("registrationFailed.html", error="Username and password must not contain any of the following characters: , ; ' \" :")

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
    held = False
    db = sqlite3.connect("main.db")
    cur = db.cursor()
    rows = cur.execute("SELECT * FROM items WHERE id = ?;", (id,))
    for row in rows:
        name = row[1].title()
        buyLimit = row[2]
        description = row[3]
    #Check if the item is held by the player
    if "user_id" in session.keys():
        rows = cur.execute("SELECT * from holdings WHERE item_id = ? and user_id = ?;", (id, session["user_id"]))
        for row in rows:
            held = True
    db.close()
    #Render error if name not found
    if name == "NULL":
        return render_template("404error.html", error="Item not found.")
    
    #Render the item's page
    return render_template("item.html", name=name, description=description, id=id, highPrice=highPrice, lowPrice=lowPrice, buyLimit=buyLimit, held=held)

@app.route("/save", methods=["POST"])
def save():
    if not request.form.get("id"):
        return redirect("/")

    if  "user_id" not in session.keys():
        return redirect("/login")

    id = request.form.get("id")

    #Save the item to the user's holdings
    db = sqlite3.connect("main.db")
    #Ensure the item is not already saved
    present = False
    rows = db.execute("SELECT * FROM holdings WHERE item_id = ? AND user_id = ?", (id, session["user_id"],))
    for row in rows:
        present = True
    #Save the item if not saved already
    if not present:
        db.execute("INSERT INTO holdings (item_id, user_id) VALUES (?, ?)", (id, session["user_id"]))
        db.commit()
    db.close()
    #Redirect back to the item's page
    url = "/item?id=" + str(id)
    return redirect(url)

@app.route("/unsave", methods=["POST"])
def unsave():
    #Ensure an id was entered by a logged in user
    if not request.form.get("id"):
        return redirect("/")

    if "user_id" not in session.keys():
        return redirect("/login")

    id = request.form.get("id")
    db = sqlite3.connect("main.db")
    #Ensure the item is already saved
    present = False
    rows = db.execute("SELECT * FROM holdings WHERE item_id = ? AND user_id = ?", (id, session["user_id"]))
    for row in rows:
        present = True
    #Unsave the item if saved already
    if present:
        db.execute("DELETE FROM holdings WHERE item_id = ? AND user_id = ?", (id, session["user_id"]))
        db.commit()
    db.close()
    #Redirect back to the item's page
    url = "/item?id=" + str(id)
    return redirect(url)

@app.route("/remove", methods=["POST"])
def remove():
    #Ensure an id was entered by a logged in user
    if not request.form.get("id"):
        return redirect("/")

    if "user_id" not in session.keys():
        return redirect("/")

    id = request.form.get("id")
    db = sqlite3.connect("main.db")
    #Ensure the item is already saved
    present = False
    rows = db.execute("SELECT * FROM holdings WHERE item_id = ? AND user_id = ?", (id, session["user_id"]))
    for row in rows:
        present = True
    #Unsave the item if saved already
    if present:
        db.execute("DELETE FROM holdings WHERE item_id = ? AND user_id = ?", (id, session["user_id"]))
        db.commit()
    db.close()
    #Redirect back to the item's page
    return redirect("/")
