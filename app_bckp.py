import time
import csv
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

import benford as bf

import redis
from flask import Flask, request, render_template, session, redirect

app = Flask(__name__)
cache = redis.Redis(host='redis', port=6379)

conf = 95
file = "data/census_2009b"

sniffer = csv.Sniffer()
sample_bytes = 320
dialect = sniffer.sniff(open(file).read(sample_bytes))

data = pd.read_csv(file, delimiter=dialect.delimiter)
f1d = bf.first_digits(data['7_2009'], digs=1, confidence=conf)
f1d_sorted = f1d.sort_index()
f1d_sorted['color'] = f1d_sorted['Z_score'].apply(
    lambda x: 'green' if x > 1.65 else 'red')

f1d['percent'] = 100*(f1d['Found']-f1d['Expected'])/f1d['Expected']
width = 0.3
ind = np.arange(1, 10)
plt.figure(figsize=(15, 5))
color = ['orange ']
plt.xticks(ind)
plt.bar(ind, f1d_sorted['Found'], width=width*0.9,
        label='Found', color=f1d_sorted['color'], alpha=0.7)
plt.bar(ind+width, f1d_sorted['Expected'], width=width *
        0.9, label='Expected', color='blue', alpha=0.7)
plt.title('Benford')
plt.legend()
plt.grid()
plt.savefig('static/images/a.png')

benf = bf.Benford((data, '7_2009'))
# benRpt = benf.F1D.report()
benPlt = benf.F1D.show_plot()


def get_hit_count():
    retries = 5
    while True:
        try:
            return cache.incr('hits')
        except redis.exceptions.ConnectionError as exc:
            if retries == 0:
                raise exc
            retries -= 1
            time.sleep(0.5)


@app.route('/', methods=("POST", "GET"))
def html_table():

    return render_template('simple.html',
                           benford=[f1d.to_html()],)


@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r
