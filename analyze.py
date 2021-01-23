"""
Reads txt files of all papers and computes tfidf vectors for all papers.
Dumps results to file tfidf.p
"""
import os
import tqdm
import pickle
from random import shuffle, seed

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from utils import Config, safe_pickle_dump

seed(1337)
max_train = 5000  # max number of tfidf training documents (chosen randomly), for memory efficiency
max_features = 5000

# read database
paper_db = pickle.load(open(Config.db_path, "rb"))

# read all text files for all papers into memory
documents = []
with tqdm.tqdm(paper_db.items()) as pbar:
    for pid, paper in pbar:
        idvv = f"{paper['_rawid']}v{paper['_version']}"
        txt_path = os.path.join("data", "txt", idvv) + ".pdf.txt"
        try:
            with open(txt_path, "rb") as f:
                n_chars = len(f.read().decode('utf-8', 'replace'))

        except FileNotFoundError:
            # some pdfs dont translate to txt
            pbar.write(f"could not find {txt_path} in txt folder.")
            continue

        pbar.set_description(f"{idvv} with {n_chars} chars")
        if 1000 < n_chars < 500000:  # 500K is VERY conservative upper bound
            # todo later: maybe filter or something some of them
            documents.append((idvv, txt_path))
        else:
            pbar.write(f"skipped {idvv} with {n_chars} chars: suspicious!")

pids, txt_paths = zip(*documents)
print(f"in total read in {len(txt_paths)} text"
      f" files out of {len(paper_db)} db entries.")

# compute tfidf vectors with scikits
v = TfidfVectorizer(
    input="filename",  # input="content",
    encoding="utf-8",
    decode_error="replace",
    strip_accents="unicode",
    lowercase=True,
    analyzer="word",
    stop_words="english",
    token_pattern=r"(?u)\b[a-zA-Z_][a-zA-Z0-9_]+\b",
    ngram_range=(1, 2),
    max_features=max_features,
    norm="l2",
    use_idf=True,
    smooth_idf=True,
    sublinear_tf=True,
    max_df=1.0,
    min_df=1,
)


# train
n_train = min(len(txt_paths), max_train)
print(f"training on {n_train} documents...")

# duplicate, shuffle, split and train, then transform
train_txt_paths = list(txt_paths)
shuffle(train_txt_paths)
v.fit(train_txt_paths[:n_train])

print(f"transforming {len(txt_paths)} documents...")
X = v.transform(txt_paths)

print(v.vocabulary_)
print(X.shape)

# write full matrix out, this one is heavy!
print("writing", Config.tfidf_path)
safe_pickle_dump({"X": X}, Config.tfidf_path)

# writing lighter metadata information into a separate (smaller) file
print("writing", Config.meta_path)
safe_pickle_dump({
    'vocad': v.vocabulary_,
    'idf': v._tfidf.idf_,
    'pids': pids,  # a full idvv string (id and version number)
    'ptoi': {x: i for i, x in enumerate(pids)}  # pid to ix in X mapping
}, Config.meta_path)

print("precomputing nearest neighbor queries in batches...")
X = X.todense()  # originally it's a sparse matrix
sim_dict = {}
batch_size = 200
for i in tqdm.trange(0, len(pids), batch_size):
    i1 = min(len(pids), i + batch_size)
    xquery = X[i:i1]  # BxD
    ds = -np.asarray(np.dot(X, xquery.T))  # NxD * DxB => NxB
    IX = np.argsort(ds, axis=0)  # NxB
    for j in range(i1 - i):
        sim_dict[pids[i + j]] = [pids[q] for q in list(IX[:50, j])]

print("writing", Config.sim_path)
safe_pickle_dump(sim_dict, Config.sim_path)
