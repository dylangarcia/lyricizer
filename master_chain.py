import glob
import os
import markovify
import requests
from bs4 import BeautifulSoup
from pprint import pprint
from contextlib import suppress

def get_artist_id_by_name(artist_name):
    s = requests.Session()
    url = "https://genius.com/api/search/multi?per_page=1&q={}".format(artist_name)
    resp = s.get(url=url).json()
    for section in resp["response"]["sections"]:
        if section["type"] not in ("top_hit", "artist"): continue
        for hit in section["hits"]:
            if section["type"] not in ("artist"): continue
            result = hit["result"]
            if result["name"].lower() == artist_name.lower():
                return result["id"]
    return None

def download_lyrics_by_artist_name(artist_name, start_page=1, end_page=3):
    s = requests.Session()
    artist_id = get_artist_id_by_name(artist_name)
    if not artist_id:
        with suppress(Exception):
            print("{} does not have an ID - creating a 404 for it".format(artist_name))
            create_404(artist_name)
            return
    with suppress(Exception):
        print("{} has an ID of {}".format(artist_name, artist_id))
    def get_page(page):
        url = "https://genius.com/api/artists/{artist_id}/songs?page={page}&sort=popularity".format(artist_id=artist_id, page=page)
        resp = s.get(url=url).json()
        return resp
    def extract_songs(page):
        with suppress(Exception):
            return [song for song in page["response"]["songs"] if song["lyrics_state"] == "complete"]
        return []
    def get_lyrics(song):
        url = song["url"]
        artist = song["primary_artist"]["name"]
        title = song["title"]
        path = "./Sources/{artist}/{title}.txt".format(artist=artist, title=title)
        if os.path.exists(path):
            print("Already downloaded {} - {}".format(artist, title))
            return
        resp = s.get(url=url).text
        bs = BeautifulSoup(resp, "html5lib")
        lyrics_div = bs.find_all("a", {"class": "referent"})
        lyrics = bs.find("div", {"class": "lyrics"}).get_text().split("\n")
        for lyric in lyrics:
            if "[" in lyric or len(lyric) == 0 or lyric.isspace(): 
                lyrics.remove(lyric)
                continue
            lyric = lyric.replace("\"", "").strip()
        return lyrics
    def save_lyrics(song, lyrics):
        artists = set([artist_name, song["primary_artist"]["name"]])
        title = song["title"]
        lyrics = "\n".join(lyrics)
        for char in ":<>!?\"'/":
            title = title.replace(char, "")
        for artist in artists:
            path = "./Sources/{artist}/".format(artist=artist)
            if not os.path.exists(path):
                os.makedirs(path)
            path += "{title}.txt".format(title=title)
            with open(path, "w", encoding="utf-8", errors="ignore") as f:
                f.write(lyrics)
            with suppress(Exception):
                print("Downloaded {} - {}".format(artist, title))
    pages = [get_page(page) for page in range(start_page, end_page + 1)]
    for page in pages:
        songs = extract_songs(page)
        for song in songs:
            lyrics = get_lyrics(song)
            if not lyrics: continue
            save_lyrics(song, lyrics)

def get_downloaded_songs(artist):
    path = "./Sources/{}".format(artist)
    if not os.path.exists(path) or len(list(glob.glob("./Sources/{}/*.txt".format(artist)))) < 5:
        print("{} does not have any downloaded songs. Downloading now".format(artist))
        download_lyrics_by_artist_name(artist)
    files = []
    for file in glob.glob("{}/*.txt".format(path)):
        files.append(file)
    return files

def make_chain(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        data = f.read()
        if not data: return
        with suppress(Exception):
            chain = markovify.NewlineText(data)
            return chain

def make_chains(artist):
    chains = []
    for path in get_downloaded_songs(artist):
        chain = make_chain(path)
        if not chain: continue
        chains.append(chain)
    return chains

def make_master_chain(artist):
    chains = make_chains(artist)
    try:
        master_chain = markovify.combine(chains)
        save_chain(artist, master_chain)
    except Exception as e:
        create_404(artist)

_404_PATH = "./Sources/404/"
def create_404(artist="404"):
    if not os.path.exists(_404_PATH):
        os.makedirs(_404_PATH)
    with open("{}{}.txt".format(_404_PATH, artist), "w") as f:
        f.write("")

def has_404(artist):
    return os.path.exists("{}{}.txt".format(_404_PATH, artist))

def get_master_chain(artist, regenerate=False):
    path = "./Master Chains/{}.json".format(artist)
    artist_files = glob.glob("./Sources/{}/*.txt".format(artist))

    if len(list(artist_files)) <= 5 and "National Championship Game" not in artist:
        regenerate = True
    if has_404(artist):
        print("{} has a 404".format(artist))
        return
    if os.path.exists(path) and not has_404(artist) and not regenerate:
        print("{} has a Master Chain\n".format(artist))
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return markovify.NewlineText.from_json(f.read())
    else:
        print("{} does not have a Master Chain, creating it now\n".format(artist))
        make_master_chain(artist)
        return get_master_chain(artist)

def save_chain(artist, chain):
    path = "./Master Chains/"
    if not os.path.exists(path):
        os.makedirs(path)
    path += "{}.json".format(artist)
    print("Saved a new Master Chain: {}".format(path))
    with open(path, "w") as f:
        f.write(chain.to_json())
        return chain
