"""
Use imagemagick to convert all pdfs to a sequence of thumbnail images.

Details
-------
Take first 8 pages of the pdf ([0-7]), tile them horizontally, using JPEG
compression 80 and triming the borders of each image.

Requires
--------
on ubuntu: `sudo apt-get install imagemagick`
on mac highsierra:
```bash
# manually install imagemagick form site
# edit ~/.bash_profile as instructed on imagemagick site
install berw install freetype
brew install --cask xquartz
```
"""

import os
import sys
import tqdm
import shutil

from tempfile import TemporaryDirectory
from subprocess import run
from subprocess import Popen, TimeoutExpired, DEVNULL

from utils import Config

# make sure imagemagick is installed
if not shutil.which("convert"):  # shutil.which needs Python 3.3+
    print(
        "ERROR: you don't have imagemagick installed.\n"
        "Install it first before calling this script"
    )
    sys.exit()

# create if necessary the directories we're using for processing and output
os.makedirs(Config.tmp_dir, exist_ok=True)
os.makedirs(Config.thumbs_dir, exist_ok=True)

# iterate over all pdf files and create the thumbnails
root, _, filenames = next(os.walk(os.path.join("data", "pdf")))
for i, filename in enumerate(tqdm.tqdm(filenames)):
    pdf_path = os.path.join(root, filename)
    thumb_path = os.path.join(Config.thumbs_dir, filename + ".jpg")
    if os.path.isfile(thumb_path):
        tqdm.tqdm.write(f"skipping {pdf_path}, thumbnail already exists.")
        continue

    if not filename.endswith('.pdf'):
        continue

    with TemporaryDirectory(dir=Config.tmp_dir) as tmpdir:
        # montage {pdf_path}[0-7] -mode Concatenate -tile x1
        #  -quality 80 -resize x230 -trim thumbs/{f}.jpg
        try:
            # generate thumbnails of pages 1-8: thumb-0.png .. thumb-7.png
            pp = Popen([
                "convert",
                f"{pdf_path}[0-7]", "-thumbnail", "x156",
                os.path.join(tmpdir, "thumb.png")
            ], stdout=DEVNULL, stderr=DEVNULL)

            # convert can unfortunately enter an infinite loop, so we wait
            ret = pp.wait(timeout=20)

        except TimeoutExpired:
            pp.terminate()
            print("convert command did not terminate in 20 seconds, terminating.")

        if os.path.isfile(os.path.join(tmpdir, "thumb-0.png")):
            # tile images horizontally
            run([
                "montage",
                "-mode", "concatenate", "-quality", "80", "-tile", "x1",
                os.path.join(tmpdir, "thumb-*.png"), thumb_path
            ], capture_output=True)

        else:
            run([
                "cp", os.path.join("static", "missing.jpg"), thumb_path
            ], capture_output=True)
            # we can also let HTML+JS handle nonexistent thumbnails
            print("could not render pdf, defaulting to a placeholder")
