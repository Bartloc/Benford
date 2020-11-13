import time
import csv
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

import benford as bf

from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import os
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'


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


@app.route("/")
def upload_file():
    return render_template('upload.html')


@app.route('/uploader', methods=['GET', 'POST'])
def uploaded_file():
    if request.method == 'POST':

        f = request.files['file']
        file = os.path.join(
            app.config['UPLOAD_FOLDER'], secure_filename(f.filename))
        f.save(file)

        delimiter = Sniff_File(file)
        data = Collect_Num_Data(file, delimiter)

        conf = 95
        f1d = bf.first_digits(data.iloc[:, 0], digs=1, confidence=conf)
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

        #benf = bf.Benford((data, '7_2009'))
        # benRpt = benf.F1D.report()
        #benPlt = benf.F1D.show_plot()

        return render_template('simple.html',
                               benford=[f1d.to_html()],)


if __name__ == '__main__':
    app.run(debug=True)
