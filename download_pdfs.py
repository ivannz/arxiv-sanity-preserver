import os
import tqdm
import time
import pickle
import shutil
import random
from urllib.request import urlopen

from utils import Config

timeout_secs = 10  # after this many seconds we give up on a paper
os.makedirs(Config.pdf_dir, exist_ok=True)

paper_db = pickle.load(open(Config.db_path, "rb"))

numok, numtot = 0, 0
with tqdm.tqdm(paper_db.items()) as pbar:
    for pid, paper in pbar:

        pdfs = [x["href"] for x in paper["links"]
                if x["type"] == "application/pdf"]
        assert len(pdfs) == 1

        pdf_url = pdfs[0] + ".pdf"
        _, basename = pdf_url.rsplit("/", 1)
        filename = os.path.join(Config.pdf_dir, basename)

        pbar.set_description(pdf_url)
        numtot += 1

        # try retrieve the pdf
        try:
            if not os.path.isfile(filename):
                req = urlopen(pdf_url, None, timeout_secs)
                with open(filename, "wb") as fp:
                    shutil.copyfileobj(req, fp)

                time.sleep(0.05 + random.uniform(0, 0.1))

            else:
                pbar.write(f"{filename} exists, skipping")

        except Exception as e:
            pbar.write(f'error downloading {pdf_url}: {str(e)}')
            continue

        numok += 1

print(f"final number of papers downloaded okay: {numok}/{len(paper_db)}")
