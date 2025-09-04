from pymongo import MongoClient
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen

from typing import NamedTuple

class Pokemon_Moves(NamedTuple):
    name: str
    type: str
    category: str
    power: int
    accuracy: int
    pp: int
    effect: str
    prob: int
  

client = MongoClient('mongodb://localhost:27017/')
db = client['pokemon_db']
moves_collection = db['pokemon_moves']

url = 'https://pokemondb.net/move/all'
request = Request(
    url,
    headers={'User-Agent': 'Mozilla/5.0'}
)

page = urlopen(request)
page_content_bytes = page.read()
page_html = page_content_bytes.decode("utf-8")

soup = BeautifulSoup(page_html, "html.parser")

pokemon_moves = soup.find("table", id="moves").find("tbody").find_all("tr")
moves_collection.create_index("name", unique=True)


for moves in pokemon_moves[0:65]:           # first 6 for testing
    moves_data = moves.find_all("td")
    
    move_name = moves_data[0].get_text().strip()
    move_type = moves_data[1].get_text().strip()

    try:
        move_category = moves_data[2].find("img")["src"]
    except:
        move_category = "N/A"

    move_pwr = moves_data[3].get_text().strip()
    move_acc = moves_data[4].get_text().strip()
    move_pp = moves_data[5].get_text().strip()
    move_effect = moves_data[6].get_text().strip()
    move_prob = moves_data[7].get_text().strip()

    poke_move = Pokemon_Moves(
        name = move_name,
        type = move_type,
        category = move_category,
        power = int(move_pwr) if move_pwr.isdigit() else 0,
        accuracy = int(move_acc) if move_acc.isdigit() else 0,
        pp = int(move_pp) if move_pp.isdigit() else 0,
        effect = move_effect,
        prob = int(move_prob) if move_prob.isdigit() else 0
    )

    # Upsert into collection (using name as primary key)
    moves_collection.update_one(
        {"name": poke_move.name},        # search by move name
        {"$set": poke_move._asdict()},   # update fields
        upsert=True                      # insert if not exists
    )

    print(f"Updated/Saved move: {poke_move.name}")
