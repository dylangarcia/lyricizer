# -*- coding: utf-8 -*-
from flask import Flask
from flask import render_template
from flask import request
from flask import url_for
from flask import send_from_directory
from flask import g
from master_chain import get_master_chain
from master_chain import create_404
from flask_cache import Cache

import markovify
import glob
import os

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.before_first_request
def before_first_request():
    create_404()

@cache.cached(timeout=60)
@app.route("/", methods=["POST", "GET"])
def index():
    path = "./Sources"
    globs = glob.glob("{}/*/".format(path))
    sources = []
    for source in globs:
        file_count = len(list(glob.glob(source + "*.txt")))
        source = source.replace(path, "").replace("\\", "").replace("!", "").replace("/", "").replace("/", "")
        if os.path.exists("{}/404/{}.txt".format(path, source)): continue
        sources.append((source, file_count))
    sources = sorted(sources, key=lambda source: source[1], reverse=True)
    sources = sorted(sources, key=lambda source: source[0])
    sources = filter(lambda tup: tup[1] > 10, sources)
    sources = [source for source, _count in sources]

    source = request.values.get("source", "National Championship Game")
    sources.insert(0, "National Championship Game")
    if source in sources:
        sources.remove(source)
    sources.insert(0, source)
    model = get_master_chain(source)
    
    sentences = []
    start_word = request.values.get("start", "")
    num_comments = request.values.get("num", 10)
    if not num_comments.isdigit():
        num_comments = 10
    if model:
        if start_word:
            try:
                sentences = [model.make_sentence_with_start(start_word, tries=15) for _ in range(num_comments)]
            except Exception as e:
                pass
        else:
            sentences = [model.make_short_sentence(140, tries=15) for _ in range(num_comments)]
    return render_template("index.html", sentences=sentences, start_word=start_word, sources=sources, source=source)

# http://flask.pocoo.org/docs/0.12/patterns/favicon/
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static"), "favicon.ico", mimetype='image/vnd.microsoft.icon')