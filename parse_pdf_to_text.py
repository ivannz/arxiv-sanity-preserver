"""
Very simple script that simply iterates over all files `data/pdf/f.pdf` and
creates a file `data/txt/f.pdf.txt` that contains the raw text, extracted
using the "pdftotext" command. If a pdf cannot be converted, this script will
produce an empty output file.
"""

import os
import sys
import time
import tqdm
import shutil

from subprocess import run

from utils import Config

# make sure pdftotext is installed
if not shutil.which("pdftotext"):  # needs Python 3.3+
    print(
        "ERROR: you don't have pdftotext installed."
        " Install it first before calling this script."
    )
    sys.exit()

_, _, filenames = next(os.walk(Config.pdf_dir))
os.makedirs(Config.txt_dir, exist_ok=True)

for i, filename in enumerate(tqdm.tqdm(filenames), start=1):
    txt_filename = filename + ".txt"
    txt_path = os.path.join(Config.txt_dir, txt_filename)
    if os.path.isfile(txt_path):
        tqdm.tqdm.write(
            f"skipping {txt_filename}, already exists.")
        continue

    pdf_path = os.path.join(Config.pdf_dir, filename)
    run(["pdftotext", "-enc", "UTF-8", pdf_path, txt_path],
        capture_output=True)

    # check output was made
    if not os.path.isfile(txt_path):
        # create an empty file, indicating that we have tried to convert
        open(txt_path, 'wb').close()

        # there was an error with converting the pdf
        tqdm.tqdm.write(
            f"there was a problem with parsing {pdf_path}"
            " to text, creating an empty text file.")
