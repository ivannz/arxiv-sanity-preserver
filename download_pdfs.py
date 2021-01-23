import os
import time
import pickle
import shutil
import random
from urllib.request import urlopen

from utils import Config

timeout_secs = 10  # after this many seconds we give up on a paper
os.makedirs(Config.pdf_dir, existok=True)

have = set(os.listdir(Config.pdf_dir))  # get list of all pdfs we already have

numok = 0
numtot = 0

paper_db = pickle.load(open(Config.db_path, "rb"))
for pid, paper in paper_db.items():

    pdfs = [x["href"] for x in paper["links"]
            if x["type"] == "application/pdf"]
    assert len(pdfs) == 1

    pdf_url = pdfs[0] + ".pdf"
    _, basename = pdf_url.rsplit("/", 1)
    fname = os.path.join(Config.pdf_dir, basename)

    # try retrieve the pdf
    numtot += 1
    try:
        if basename in have:
            print(f"fetching {pdf_url} into {fname}")
            req = urlopen(pdf_url, None, timeout_secs)
            with open(fname, "wb") as fp:
                shutil.copyfileobj(req, fp)

            time.sleep(0.05 + random.uniform(0, 0.1))
        else:
            print(f"{fname} exists, skipping")
        numok += 1
    except Exception as e:
        print("error downloading: ", pdf_url)
        print(e)
    print(f"{numok}/{numtot} of {len(paper_db)} downloaded ok.")

print("final number of papers downloaded okay: {numok}/{len(paper_db)}")
