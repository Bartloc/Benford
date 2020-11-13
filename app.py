import time
import csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
import pathlib

import benford as bf

from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import os


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
DISALLOWED_EXTENSIONS = {'exe', 'dll', 'php', 'pdf'}


def Sniff_File(file):
    sniffer = csv.Sniffer()
    sample_bytes = 320
    dialect = sniffer.sniff(open(file).read(sample_bytes))
    return dialect.delimiter


def Collect_Num_Data(file, delimiter):
    data_all = pd.read_csv(file, delimiter=delimiter)
    numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
    data = data_all.select_dtypes(include=numerics)
    return data


def allowed_file(filename):
    return False if pathlib.Path(filename).suffix in DISALLOWED_EXTENSIONS else True


@app.route("/")
def upload_file():
    return render_template('form.html')


@app.route('/benford', methods=['GET', 'POST'])
def uploaded_file():
    if request.method == 'POST':

        f = request.files['file']

        if not allowed_file(f.filename):
            return 'Wrong file extension', 200

        file = os.path.join(
            app.config['UPLOAD_FOLDER'], secure_filename('data'))
        f.save(file)

        delimiter = Sniff_File(file)
        data = Collect_Num_Data(file, delimiter)

        conf = 95
        f1d = bf.first_digits(data.iloc[:, 0], digs=1, confidence=conf)
        f1d['percent'] = 100*(f1d['Found']-f1d['Expected'])/f1d['Expected']
        f1d_sorted = f1d.sort_index()
        f1d_sorted['color'] = f1d_sorted['percent'].apply(
            lambda x: 'green' if abs(x) < 5 else 'red')

        width = 0.3
        ind = np.arange(1, 10)
        plt.figure(figsize=(15, 5))
        plt.xticks(ind)
        p1 = plt.bar(ind, f1d_sorted['Found'], width=width*0.9,
                     label='Found', color=f1d_sorted['color'], alpha=0.7)
        p2 = plt.bar(ind+width, f1d_sorted['Expected'], width=width *
                     0.9, label='Expected', color='blue', alpha=0.7)

        patchMatch = mpatches.Patch(color='green', label='Match - 95% ')
        patchNoMatch = mpatches.Patch(
            color='red', label='No Match - less tha 95%')
        plt.title('Benford')

        plt.legend(handles=[patchMatch, patchNoMatch, p2])
        plt.grid()
        plt.savefig('static/images/benford.png')

        return render_template('benford.html',
                               benford=[f1d.to_html()])


@app.errorhandler(csv.Error)
def handle_empty_data(args):
    return 'Cannot read data. Try to change delimiter.', 200


@app.errorhandler(pd.errors.ParserError)
def handle_empty_data(args):
    return 'Failed parsing Input', 200


if __name__ == '__main__':
    app.run(debug=True)
