from pymongo import MongoClient
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen

from typing import List, NamedTuple

class Pokemon(NamedTuple):
    id: int
    name: str
    avatar: str
    details_path: str
    types: List[str]
    total: int
    hp: int
    attack: int
    defense: int
    sp_attack: int
    sp_defense: int
    speed: int
    entry: str
    moves: List[str]

client = MongoClient('mongodb://localhost:27017/')
db = client['pokemon_db']
collection = db['pokemons']

url = 'https://pokemondb.net/pokedex/all'
request = Request(
    url,
    headers={'User-Agent': 'Mozilla/5.0'}
)

page = urlopen(request)
page_content_bytes = page.read()
page_html = page_content_bytes.decode("utf-8")

soup = BeautifulSoup(page_html, "html.parser")

pokemon_rows = soup.find("table", id="pokedex").find("tbody").find_all("tr")
for pokemon in pokemon_rows[0:5]:  # first 5 for testing
    pokemon_data = pokemon.find_all("td")
    poke_id = pokemon_data[0]['data-sort-value']

    # image
    img_tag = pokemon_data[0].find("img")
    avatar = img_tag["src"] if img_tag else None

    # name (main name or alternative form)
    name_cell = pokemon_data[1]
    main_name = name_cell.find("a").get_text()
    alt_name = name_cell.find("small").get_text() if name_cell.find("small") else None

    name = alt_name if alt_name else main_name



    # details page link
    details_uri = pokemon_data[1].find("a")["href"]
    entry_url = f'https://pokemondb.net{details_uri}'

    # types
    types = [t.get_text() for t in pokemon_data[2].find_all("a")]

    # stats
    total     = pokemon_data[3].get_text()
    hp        = pokemon_data[4].get_text()
    attack    = pokemon_data[5].get_text()
    defense   = pokemon_data[6].get_text()
    sp_attack = pokemon_data[7].get_text()
    sp_defense= pokemon_data[8].get_text()
    speed     = pokemon_data[9].get_text()

    request = Request(
        entry_url,
        headers={'User-Agent': "Mozilla/5.0"}
    )

    entry_page_html = urlopen(request).read().decode("utf-8")
    entry_soup = BeautifulSoup(entry_page_html, "html.parser")
    
    try:
        entry_text = entry_soup.find_all("main")[0].find_all("div",{"class":"resp-scroll"})[2].find_all("tr")[0].find_all("td")[0].getText()

    except:
        entry_text = "N/A"

    learnable_moves = entry_soup.find_all("main")[0].find_all("div",{"class":"tabset-moves-game sv-tabs-wrapper"})[0].find_all("tr")

    move_set = []
    for i in range(1, len(learnable_moves)):
        try:
            move = learnable_moves[i].find_all("a",{"class": "ent-name"})[0].getText()
            if move not in move_set:
                move_set.append(move)
        except (IndexError, AttributeError) as e:
            #print(f"Skipping index {i}: {e}")
            continue
            
    typed_pokemon = Pokemon(
        id = int(poke_id),
        name = name,
        avatar= avatar,
        details_path= details_uri,
        types= types,
        total= int(total),
        hp = int(hp),
        attack= int(attack),
        defense= int(defense),
        sp_attack= int(sp_attack),
        sp_defense= int(sp_defense),
        speed= int(speed),
        entry= entry_text,
        moves = move_set


    )

    
    if alt_name:
        unique_id = f"{poke_id}-{alt_name.lower().replace(' ', '-')}"
        typed_pokemon = typed_pokemon._replace(id=unique_id)

    collection.update_one(
    {"id": typed_pokemon.id},
    {"$set": typed_pokemon._asdict()},
    upsert=True
    )


    print(f"Saved Pokémon {typed_pokemon.id}: {typed_pokemon.name}")



    
