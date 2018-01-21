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
import time

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.before_first_request
def before_first_request():
    create_404()

@app.before_request
def before_request():
    g.request_start_time = time.time()
    g.request_time = lambda: "%.5fs" % (time.time() - g.request_start_time)

@cache.cached(timeout=60)
@app.route("/", methods=["POST", "GET"])
def index():
    path = "./Sources"
    globs = glob.glob("{}/*/".format(path))
    sources = []
    for source in globs:
        source = source.replace(path, "").replace("\\", "").replace("!", "").replace("/", "").replace("/", "")
        if os.path.exists("{}/404/{}.txt".format(path, source)): continue
        print(source + "*.txt")
        if len(list(glob.glob(source + "{}*.txt"))) <= 10: continue
        sources.append(source)
    source = request.values.get("source", "National Championship Game")
    if source in sources:
        sources.remove(source)
    sources.insert(0, source)
    model = get_master_chain(source)
    
    sentences = []
    start_word = request.values.get("start", "")
    if model:
        if start_word:
            try:
                sentences = [model.make_sentence_with_start(start_word, tries=15) for _ in range(5)]
            except Exception as e:
                pass
        else:
            sentences = [model.make_short_sentence(140, tries=15) for _ in range(5)]
    return render_template("index.html", sentences=sentences, start_word=start_word, sources=sources, source=source)

# http://flask.pocoo.org/docs/0.12/patterns/favicon/
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(url_for("static", filename="favicon.ico"), mimetype='image/vnd.microsoft.icon')