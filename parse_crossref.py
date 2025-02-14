####################################################################
#
# This file is part of exfor-parser.
# Copyright (C) 2025 International Atomic Energy Agency (IAEA)
#
# Disclaimer: The code is still under developments and not ready
#             to use. It has been made public to share the progress
#             among collaborators.
# Contact:    nds.contact-point@iaea.org
#
####################################################################


import requests
import pandas as pd
import numpy as np
import logging
from difflib import SequenceMatcher

from .data_manage import filter_entries_without_doi

"""
This program is to get #doi using the title and the name of the first author from Crossref API for the EXFOR entries without doi information.

Example query using Crossref API:
    https://api.crossref.org/works?query.title=18O+48Ti%20elastic%20and%20inelastic%20scattering%20at%20275%20MeV&query.bibliographic=2024,Brischetto.&select=title,author,DOI&rows=20
    Note that there is no limitation to use CrossRef API, but the contact mailto must be added to the request header. 

See more details:
    https://api.crossref.org/swagger-ui/index.html
    https://www.crossref.org/documentation/retrieve-metadata/rest-api/
    https://www.crossref.org/guestquery/
"""


BASE_URL = "https://api.crossref.org/works?"

headers = {
    "User-Agent": "IAEA NDS (https://nds.iaea.org/; mailto:nds.contact-point@iaea.org) EXFOR_BIB_Parser/1.0",
    "X-Rate-Limit-Limit": 20,
    "X-Rate-Limit-Interval": "1s",
}

max_result = 5
selections = "title,author,DOI"

logging.basicConfig(filename="doi_parsing.log", level=logging.DEBUG, filemode="w")


def similarity(a, b):
    seq = SequenceMatcher(None, a=a, b=b)
    return seq.ratio()


def get_doi_from_crosreff(exfor_bib):
    url = f"{BASE_URL}query.title={exfor_bib['title']}&query.bibliographic={exfor_bib['first_author'].split('.')[-1]},{exfor_bib['year']}&select={selections}&rows={max_result}"

    response = requests.get(url, headers={})
    if response.status_code != 200:
        logging.error(f"ERROR: at ENTRY: {exfor_bib['entry']}, {response.status_code} {response.reason}")

    else:
        r = response.json()

    titles = [
        i["title"][0] if i.get("title") else None
        for i in r["message"]["items"][:max_result]
    ]
    dois = [
        i["DOI"] if i.get("DOI") else None
        for i in r["message"]["items"][:max_result]
    ]
    authors = [
        i["author"] if i.get("author") else []
        for i in r["message"]["items"][:max_result]
    ]
    first_author = [ a[0]["family"] if a and a[0].get("family") else "unknown" for a in authors  ]

    ## The Crossref API return with max_result will be stored into DataFrame
    df = pd.DataFrame(
        {
            "exfor_entry": exfor_bib["entry"],
            "exfor_title": exfor_bib["title"],
            "exfor_first_author": exfor_bib["first_author"],
            "exfor_main_reference": exfor_bib["main_reference"],
            "crossref_title": titles,
            "crossref_doi": dois,
            "crossref_first_author": first_author,
        }
    )

    ## Similarity check between the title in EXFOR and the titles of API return
    df["title_similarity"] = df.apply(
        lambda x: similarity(
            exfor_bib["title"].title(), x["crossref_title"]), 
            axis=1
    )

    ## Similarity check between the name of first author in EXFOR and that of API return
    df["author_similarity"] = df.apply(
        lambda x: similarity(
            exfor_bib["first_author"].split(".")[-1].title(), x["crossref_first_author"]),
            axis=1,
    )

    ## Get highest similarity score with title
    most_probable_paper = pd.DataFrame(
        [df.iloc[df["title_similarity"].idxmax()].to_dict()]
    )

    ## Store as text for all 5 results for each entry
    df.to_csv(
        r"probables.txt", header=None, index=None, sep=" ", mode="a"
    )

    ## Return as a DataFrame
    return most_probable_paper


def final_decision(df):
    df["flag"] = np.where(
        (df["title_similarity"] > 0.8) & (df["author_similarity"] > 0.8), True, False
    )
    return df[df["flag"] == True]


def process_all():
    ## List of entry bib dictionaries
    exfor_bib_list = filter_entries_without_doi().to_dict("records")

    ## New dataframe to store the API return
    probable_df = pd.DataFrame(
        columns=[
            "exfor_entry",
            "exfor_title",
            "exfor_first_author",
            "exfor_main_reference",
            "crossref_title",
            "crossref_doi",
            "crossref_first_author",
            "title_similarity",
            "author_similarity",
        ]
    )

    for index, exfor_bib in enumerate(exfor_bib_list):
        print(index, "/", len(exfor_bib_list), exfor_bib["entry"])
        if not exfor_bib.get("title") or not exfor_bib.get("first_author"):
            ## There are entries without TITLE (e.g. 11852)
            continue

        try:
            most_probable_paper = get_doi_from_crosreff(exfor_bib)
            probable_df = pd.concat([probable_df, most_probable_paper], ignore_index=True)

        except KeyboardInterrupt:
            break

        except:
            logging.error(f"ERROR: at ENTRY: {exfor_bib['entry']}", exc_info=True)

    ## Store the most probable one for each entry in pickle and json file
    probable_df.to_pickle("data/probable.pickle")
    probable_df.to_json("data/probable.json", orient="records", indent=1)

    ## Filter the one if the title_similarity and author_similarity scores are both > 0.8
    crossref_df = final_decision(probable_df)
    crossref_df = crossref_df.sort_values(by=['exfor_entry'])
    crossref_df.to_pickle("data/crossref.pickle")
    crossref_df.to_json("data/crossref.json", orient="records", indent=1)

    return crossref_df



def process_one(exfor_bib):
    df = get_doi_from_crosreff(exfor_bib)
    if not df[ (df["title_similarity"] > 0.8) & (df["author_similarity"] > 0.8)].empty:
        print ( df.values )


if __name__ == "__main__":
    process_all()
