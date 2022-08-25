# OSRS-Tracker
This is a web app that allows for price tracking of the Grand Exchange items on the MMORPG, Old School Runescape.

## Why is this needed?
The Grand Exchange is a commodity exchange for all tradeable items found in the game. Many players make a lot of in-game money by trading (or flipping) items on the Grand Exchange. Unfortunately, there is not a way to track prices built into the game itself except by going to the exchange location within the game world and doing manual searches for items. This website helps users track the best prices buyers and sellers get (the low and high prices of each item, respectively) without having to make a trek all the way out to Varrock.

## How was this made?
The website itself is built primarily on two frameworks, Flask and Bootstrap. The Flask backend communicates with a pricing API maintained by the developers of the Old School Runescape Wiki and saves item descriptions, pricing, and buy limits in a SQL database. Similarly, user information including usernames, hashes, and saved items is also held in a database. Bootstrap allowed for the frontend to not only be look more modern, but to incorporate responsive design principles in case users ever need to check the price of a Cadava Potion on the go.

## Special Thanks
Thanks to all of the contributors to the tools I used in making this. The Grand Exchange pricing API found <a href="https://oldschool.runescape.wiki/w/RuneScape:Real-time_Prices">here</a>, <a href="https://getbootstrap.com">Bootstrap</a>, <a href="https://flask.palletsprojects.com">Flask</a>, and even <a href="https://python.org">Python</a> itself are only possible due to largely volunteer contributors. If any of you are reading this, thank you!
