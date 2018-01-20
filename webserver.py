# -*- coding: utf-8 -*-
from flask import Flask
from flask import render_template
from flask import request
from master_chain import get_master_chain
from master_chain import create_404
import markovify
import glob
import os

app = Flask(__name__)

@app.before_first_request
def before_first_request():
    create_404()

@app.route("/", methods=["POST", "GET"])
def index():
    path = "./Sources"
    globs = glob.glob("{}/*/".format(path))
    sources = []
    for source in globs:
        source = source.replace(path, "").replace("\\", "").replace("!", "").replace("/", "").replace("/", "")
        if os.path.exists("{}/404/{}.txt".format(path, source)):
            continue
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