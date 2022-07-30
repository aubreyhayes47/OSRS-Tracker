import requests
import sqlite3

headers = {
    'User-Agent': 'Test Project - irish775#2989',
}

limits = {}

url = "https://prices.runescape.wiki/api/v1/osrs/mapping"
response = requests.get(url=url,headers=headers)
response = response.json()

#This made a dict for the names
# for dict in response:
#     names.update({dict['id']:dict['name']})

#This makes a dict for the buy limits
#The try except exists as not all items have existing buy limits
for dict in response:
    try:
        limits.update({dict['id']:dict['limit']})
    except KeyError:
        continue

#Add the limits into the items database
db = sqlite3.connect("items.db")
cur = db.cursor()
for id in limits.keys():
    cur.execute("UPDATE items SET buyLimit = ? WHERE id = ?", (limits[id], id,))

#Save changes before closing the database
db.commit()
db.close()

