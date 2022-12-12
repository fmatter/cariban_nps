from cldfbench import CLDFSpec
from cldfbench.cldf import CLDFWriter
import pandas as pd
from cldfbench_cariban_meta import Dataset
import json
import sys
from pycldf.sources import Source
import pybtex
from pathlib import Path

meta = Dataset()
full = len(sys.argv) > 1

# lg_list = ["tri", "hix", "aka", "mak"]
# # lg_list = ["tri"]
# lg_records = {}
# for lg in lg_list:
#     records = pd.read_csv(f"data/{lg}_data.csv", keep_default_na=False)
#     records["Language_ID"] = lg
#     if "Comment" in records.columns:
#         records.drop(columns="Comment", inplace=True)
#     if not full:
#         annotations = pd.read_csv(f"data/{lg}_ann.csv", keep_default_na=False)
#         custom_dict = {x: i for i, x in enumerate(list(records["ID"]))}
#         df = annotations.sort_values(by=["ID"], key=lambda x: x.map(custom_dict))

#         df = pd.merge(annotations, records, how="left", on="ID").fillna("")
#         df["Discont_NP"] = df["Value"]
#         df = df[(df["Discont_NP"] != "n") | (df["Comment"] != "")]
#         lg_records[lg] = df
#     else:
#         lg_records[lg] = records.fillna("")

if not full:
    df = pd.read_csv("data/dataset.csv", keep_default_na=False)
else:
    df = pd.read_csv("data/full_data.csv", keep_default_na=False)
with open("data/sources.txt", "r") as f:
    found_refs = f.read().split("\n")

split_cols = [
    "Analyzed_Word",
    "Analyzed_Word_Morphemes",
    "Gloss",
    "Part_Of_Speech",
]


def collect_refs(s):
    if s != "":
        found_refs.append(s.split("[")[0])


def add_audio(writer, rec):
    filename = rec["Example_ID"] + ".wav"
    path = Path("data/audio") / filename
    if path.is_file():
        writer.objects["MediaTable"].append(
            {
                "ID": rec["ID"],
                "Download_URL": f"file:data/audio/{filename}",
                "Media_Type": "wav",
            }
        )
        return rec["ID"]


def add_positions(rec):
    if rec["Positions"] != "":
        positions = [int(x) - 1 for x in rec["Positions"].split(",")]
        rec["Analyzed_Word"] = [
            "**" + x + "**" if i in positions else x
            for i, x in enumerate(rec["Analyzed_Word"])
        ]
    return rec


panare = pd.read_csv("data/panare.csv")
panare["Language_ID"] = "pan"
panare["ID"] = panare.apply(lambda x: f"pan-{x.name}", axis=1)

for col in split_cols:
    if col in panare.columns:
        panare[col] = panare[col].apply(lambda x: x.split(" "))
panare = panare.apply(add_positions, axis=1)

with CLDFWriter(
    CLDFSpec(dir="data/cldf", module="Generic", metadata_fname="metadata.json")
) as writer:
    writer.cldf.add_component("ExampleTable")
    if not full:
        writer.cldf.add_component("MediaTable")
    writer.cldf.add_columns(
        "ExampleTable",
        {
            "name": "Part_Of_Speech",
            "required": False,
            "dc:description": "Parts of speech, aligned with Analyzed_Word",
            "dc:extent": "multivalued",
            "datatype": "string",
            "separator": "\t",
        },
        {
            "name": "Source",
            "required": False,
            "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#source",
            "datatype": "string",
        },
        "Media_ID",
    )
    if not full:
        writer.cldf.add_columns(
            "ExampleTable",
            {
                "name": "Pattern",
                "required": False,
                "datatype": "string",
            },
            {
                "name": "Discontinuous",
                "required": False,
                "datatype": "string",
            },
            {
                "name": "Intervening",
                "required": False,
                "datatype": "string",
            },
            {
                "name": "Animacy",
                "required": False,
                "datatype": "string",
            },
            {
                "name": "Type",
                "required": False,
                "datatype": "string",
            },
            {
                "name": "Order",
                "required": False,
                "datatype": "string",
            },
            {
                "name": "Argument",
                "required": False,
                "datatype": "string",
            },
            {
                "name": "Role",
                "required": False,
                "datatype": "string",
            },
            {
                "name": "Genre",
                "required": False,
                "datatype": "string",
            },
        )
    writer.cldf.add_component("LanguageTable")
    for col in split_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: x.split("\t"))
            df[col] = df[col].apply(lambda x: [y if y else "…" for y in x])
    df["Primary_Text"] = df.apply(
        lambda x: " ".join(x["Analyzed_Word"]).replace("-", "")
        if x["Primary_Text"] == ""
        else x["Primary_Text"],
        axis=1,
    )
    df["Source"].map(collect_refs)
    for rec in df.to_dict("records"):
        if not full:
            if add_audio(writer, rec):
                rec["Media_ID"] = rec["ID"]
        writer.objects["ExampleTable"].append(rec)
    for rec in panare.to_dict("records"):
        writer.objects["ExampleTable"].append(rec)
    for lg in set(df["Language_ID"]):
        writer.objects["LanguageTable"].append(meta.get_lg(lg))
    writer.objects["LanguageTable"].append(meta.get_lg("pan"))

    bib = pybtex.database.parse_file("data/car.bib", bib_format="bibtex")
    sources = [
        Source.from_entry(k, e) for k, e in bib.entries.items() if k in found_refs
    ]
    writer.cldf.add_sources(*sources)

    writer.write()
