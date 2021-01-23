"""
Queries arxiv API and downloads papers (the query is a parameter).
The script is intended to enrich an existing database pickle (by default db.p),
so this file will be loaded first, and then new results will be added to it.
"""

import os
import time
import pickle
import random
import argparse
import urllib.request
import requests

import feedparser

from utils import Config, safe_pickle_dump


def encode_feedparser_dict(d):
    """
    helper function to get rid of feedparser bs with a deep copy.
    I hate when libs wrap simple things in their own classes.
    """
    if isinstance(d, feedparser.FeedParserDict) or isinstance(d, dict):
        return {k: encode_feedparser_dict(d[k]) for k in d.keys()}
    elif isinstance(d, list):
        return [encode_feedparser_dict(k) for k in d]
    else:
        return d


def parse_arxiv_url(url):
    """
    examples is http://arxiv.org/abs/1512.08756v2
    we want to extract the raw id and the version
    """
    _, idversion = url.rsplit('/', 1)
    pid, ver = idversion.rsplit('v', 1)
    return pid, int(ver)


if __name__ == "__main__":

    # parse input arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--search-query",
        type=str,
        default="cat:cs.CV OR cat:cs.AI OR cat:cs.LG OR cat:cs.CL OR cat:cs.NE OR cat:stat.ML",
        help="query used for arxiv API. See http://arxiv.org/help/api/user-manual#detailed_examples",
    )
    parser.add_argument(
        "--start-index", type=int, default=0, help="0 = most recent API result"
    )
    parser.add_argument(
        "--max-index",
        type=int,
        default=10000,
        help="upper bound on paper index we will fetch",
    )
    parser.add_argument(
        "--results-per-iteration", type=int, default=100, help="passed to arxiv API"
    )
    parser.add_argument(
        "--wait-time",
        type=float,
        default=5.0,
        help="lets be gentle to arxiv API (in number of seconds)",
    )
    parser.add_argument(
        "--break-on-no-added",
        type=int,
        default=1,
        help="break out early if all returned query papers are already in db? 1=yes, 0=no",
    )
    args = parser.parse_args()

    # lets load the existing database to memory
    paper_db = {}
    try:
        paper_db = pickle.load(open(Config.db_path, "rb"))

    except Exception as e:
        print(f"error loading existing database {str(e)}\n")
        print("starting from an empty database")
    print(f"database has {len(paper_db)} entries at start")

    # main loop where we fetch the new results
    num_added_total = 0
    print(f"Searching arXiv for {args.search_query}")
    for i in range(args.start_index, args.max_index, args.results_per_iteration):
        print(f"Results {i} - {i + args.results_per_iteration}")
        response = requests.get("http://export.arxiv.org/api/query", params={
            "search_query": args.search_query,
            "sortBy": "lastUpdatedDate",
            "start": i,
            "max_results": args.results_per_iteration
        })

        feed = feedparser.parse(response.text)
        if len(feed.entries) == 0:
            print("Received no results from arxiv. Rate limiting? "
                  "Exiting. Restart later maybe.")
            print(response.text)
            break

        num_added, num_skipped = 0, 0
        for entry in map(encode_feedparser_dict, feed.entries):
            # extract just the raw arxiv id and version for this paper
            rawid, version = parse_arxiv_url(entry["id"])
            entry["_rawid"], entry["_version"] = rawid, version

            # add to our database if we didn't have it before, or if this is a new version
            if rawid not in paper_db or version > paper_db[rawid]["_version"]:
                paper_db[rawid] = entry
                print(f"Updated {entry['updated']} added {entry['title']}")
                num_added += 1
            else:
                num_skipped += 1

        # print some information
        print("Added %d papers, already had %d." % (num_added, num_skipped))
        num_added_total += num_added

        if num_added == 0 and args.break_on_no_added == 1:
            print("No new papers were added. Assuming "
                  "no new papers exist. Exiting.")
            break

        print(f"Sleeping for {args.wait_time} seconds")
        time.sleep(args.wait_time + random.uniform(0, 3))

    # save the database before we quit, if we found anything new
    if num_added_total > 0:
        print(f"Saving database with {len(paper_db)} papers to {Config.db_path}")
        safe_pickle_dump(paper_db, Config.db_path)
