import glob
import os
import markovify
import requests
from bs4 import BeautifulSoup
from pprint import pprint

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

def download_lyrics_by_artist_name(artist_name, start_page=1, end_page=5):
    s = requests.Session()
    artist_id = get_artist_id_by_name(artist_name)
    print("{} has an ID of {}".format(artist_name, artist_id))
    def get_page(page):
        url = "https://genius.com/api/artists/{artist_id}/songs?page={page}&sort=popularity".format(artist_id=artist_id, page=page)
        resp = s.get(url=url).json()
        return resp
    def extract_songs(page):
        try:
            return [song for song in page["response"]["songs"] if song["lyrics_state"] == "complete"]
        except Exception as e:
            print(str(e), page)
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
        artist = song["primary_artist"]["name"]
        title = song["title"]
        lyrics = "\n".join(lyrics)
        for char in ":<>!?\"'/":
            title = title.replace(char, "")
        path = "./Sources/{artist}/".format(artist=artist)
        if not os.path.exists(path):
            os.makedirs(path)
        path += "{title}.txt".format(title=title)
        with open(path, "w", encoding="utf-8", errors="ignore") as f:
            f.write(lyrics)
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
        try:
            chain = markovify.NewlineText(data)
        except Exception as e:
            return
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
    master_chain = markovify.combine(chains)
    save_chain(artist, master_chain)

def get_master_chain(artist, regenerate=False):
    path = "./Master Chains/{}.json".format(artist)
    if len(list(glob.glob("./Sources/{}/*.txt".format(artist)))) <= 5 and "National Championship Game" not in artist:
        regenerate = True
    if regenerate:
        print("Generating Master Chain for {}".format(artist))
        make_master_chain(artist)
    if os.path.exists(path):
        print("{} has a Master Chain\n".format(artist))
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return markovify.NewlineText.from_json(f.read())
    print("{} does not have a Master Chain or has too few sources\n".format(artist))
    return get_master_chain(artist, True)

def save_chain(artist, chain):
    path = "./Master Chains/"
    if not os.path.exists(path):
        os.makedirs(path)
    path += "{}.json".format(artist)
    print("Saved a new Master Chain: {}".format(path))
    with open(path, "w") as f:
        f.write(chain.to_json())
        return chain