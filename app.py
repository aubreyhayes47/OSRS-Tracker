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

#Change the user agent for python requests
headers = {
    'User-Agent': 'Test Project - irish775#2989',
}

#This checks the price of an item based on id
def pricecheck(id, data):
    #Index into the data to find the high, low, highTime, and lowTime for this item
    return data[f"{id}"]
    

@app.route("/")
def home():
    #This gets the data for the abyssal whip and renders the search page
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
            return render_template("403error.html", error="no username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("403error.html", error="no password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", (request.form.get("username"),)).fetchall()
        print(rows[0])

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0][2], request.form.get("password")):
            return render_template("403error.html", error="incorrect username or password")

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
            return render_template("403error.html", error="no username")

        #Make sure it is not already registered
        for row in db.execute("SELECT * FROM users WHERE username = ?", (request.form.get("username"),)):
            return render_template("403error.html", error="username already taken")

        #Make sure neither password is blank
        if not request.form.get("password"):
            return render_template("403error.html", error="no password")
        if not request.form.get("confirmation"):
            return render_template("403error.html", error="must confirm password")

        #Make sure the passwords match
        if request.form.get("password") != request.form.get("confirmation"):
            return render_template("403error.html", error="password and confirmation must match")

        #Store the new user
        username = request.form.get("username")
        hash = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", (username, hash,))
        db.commit()
        db.close()
        return render_template("registered.html")
        #After storing the new user, render registered template which extends /login with a success message

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
    data = response["data"]
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
    try:
        id = int(search)
        ids.append(id)
        cur = db.cursor()
        rows = cur.execute("SELECT * FROM items WHERE id = ?;", (id,))

         #This moves through the result from the select and adds the id, name, and prices to the respective lists
        for row in rows:
            name = row[1]
            names.append(name)
            buyLimits.append(row[2])
            prices = pricecheck(id, data)
            highPrices.append(prices['high'])
            lowPrices.append(prices['low'])
    
    #If the search is not an integer, search for the id, name and prices based on the search term in the sql database
    except ValueError:
        cur = db.cursor()
        
        #This moves through each result from the select and adds the id, name, and prices to the respective lists
        for row in cur.execute("SELECT * FROM items WHERE name LIKE ?;", ("%"+search+"%",)):
            try:
                prices = pricecheck(row[0], data)
            except KeyError:
                continue
            ids.append(row[0])
            names.append(row[1])
            buyLimits.append(row[2])
            highPrices.append(prices['high'])
            lowPrices.append(prices['low'])
    db.close()
    return render_template("searched.html", ids=ids,names=names, highPrices=highPrices, 
    lowPrices=lowPrices, buyLimits=buyLimits, search=search)

@app.route("/item")
def item():
    #Return an error if there is no item id entered
    if not request.args.get("id"):
        return render_template("403error.html", error="item does not exist")

    #Render information based on the item id entered
    #Get the id
    id = request.args.get("id")

    #Fetch data from the API and convert to json
    url = f"https://prices.runescape.wiki/api/v1/osrs/latest?id={id}"
    response = requests.get(url=url,headers=headers)
    response = response.json()
    #Save the data as a dictionary
    data = response["data"]

    highPrice = data[str(id)]["high"]
    lowPrice = data[str(id)]["low"]

    print(data)

    #Get the item name based on id
    name = "NULL"
    db = sqlite3.connect("main.db")
    cur = db.cursor()
    rows = cur.execute("SELECT * FROM items WHERE id = ?;", (id,))
    for row in rows:
        name = row[1]
        buyLimit = row[2]
        description = row[3]
    db.close()
    #Render error if name not found
    if name == "NULL":
        return render_template("403error.html", error="item not found")
    
    #Render the item's page
    return render_template("item.html", name=name, description=description, id=id, highPrice=highPrice, lowPrice=lowPrice, buyLimit=buyLimit)
