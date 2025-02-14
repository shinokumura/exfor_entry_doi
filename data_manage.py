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

import pandas as pd

from submodules.exfor.queries import get_exfor_bib_table


def load_all_exfor_bib():
    return get_exfor_bib_table()


def filter_entries_with_doi():
    exfor_bib_df = get_exfor_bib_table()
    return exfor_bib_df[exfor_bib_df["main_doi"].notnull()]


def filter_entries_without_doi():
    exfor_bib_df = get_exfor_bib_table()
    return exfor_bib_df[exfor_bib_df["main_doi"].isnull()]



def maerge_and_output_all_doi():

    exfor_bib_df = load_all_exfor_bib()
    crossref_df = pd.read_pickle("data/crossref.pickle")
    doi_df = pd.DataFrame(
        columns=[
            "exfor_entry",
            "exfor_first_author",
            "exfor_title",
            "exfor_main_reference"
            "main_reference_doi",
            "doi_source",
        ]
    )
    doi_df = doi_df.assign(exfor_entry = exfor_bib_df["entry"],
                  exfor_first_author = exfor_bib_df["first_author"],
                  exfor_title = exfor_bib_df["title"],
                  exfor_main_reference = exfor_bib_df["main_reference"],
                  main_reference_doi = exfor_bib_df["main_doi"],
                  doi_source = None
                  )
    # doi_df = doi_df.set_index(["exfor_entry"])
    ## update method
    # dict_cr = {
    #               "exfor_entry" : crossref_df["exfor_entry"],
    #               "exfor_first_author" : crossref_df["exfor_first_author"],
    #               "exfor_title" : crossref_df["exfor_title"],
    #               "exfor_main_reference" : crossref_df["exfor_main_reference"],
    #               "main_reference_doi" : crossref_df["crossref_doi"],
    #               "doi_source" :  "Crossref"
    # }
    # doi_df.update(dict_cr)

    cr_dict = crossref_df.set_index("exfor_entry").T.to_dict("dict")


    for i, row in doi_df.iterrows():
        if row["main_reference_doi"]:
            doi_df.at[i, "doi_source"] = "EXFOR"
        if not row["main_reference_doi"] and cr_dict.get( row["exfor_entry"] ):
            doi_df.at[i, "doi_source"] = "Crossref"
            doi_df.at[i, "main_reference_doi"] = cr_dict[ row["exfor_entry"] ]["crossref_doi"]


    doi_df = doi_df.sort_values(by=['exfor_entry'])

    doi_df.to_pickle("data/doi.pickle")
    doi_df.set_index("exfor_entry").to_json("data/doi.json", orient="index", indent=1) #, indent=1)




maerge_and_output_all_doi()
