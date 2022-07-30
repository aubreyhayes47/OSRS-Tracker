import os
import requests
import sqlite3
import urllib.parse

from flask import Flask, redirect, render_template, request, session

app = Flask(__name__)

#Change the user agent for python requests
headers = {
    'User-Agent': 'Test Project - irish775#2989',
}

#This checks the price of an item based on id
def pricecheck(id, data):
    #Index into the data to find the high, low, highTime, and lowTime for this item
    return data[f"{id}"]
    

@app.route("/")
def hello_world():
    #This gets the data for the abyssal whip and renders the search page
    return render_template("index.html")

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

     #If the search term is an integer, search for the name based on the id
    try:
        id = int(search)
        ids.append(id)
        db = sqlite3.connect("items.db")
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
        db.close()
    
    #If the search is not an integer, search for the id, name and prices based on the search term in the sql database
    except ValueError:
        db = sqlite3.connect("items.db")
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
        return render_template("403error.html")

    #Render information based on the item id entered
    #Get the id
    id = request.args.get("id")

    #Get the item name based on id
    name = "NULL"
    db = sqlite3.connect("items.db")
    cur = db.cursor()
    rows = cur.execute("SELECT * FROM items WHERE id = ?;", (id,))
    for row in rows:
        name = row[1]
        description = row[3]
    db.close()

    #Render error if name not found
    if name == "NULL":
        return render_template("403error.html")
    
    #Render the item's page
    return render_template("item.html", name=name, description=description, id=id)
