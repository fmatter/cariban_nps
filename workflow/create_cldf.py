from cldfbench import CLDFSpec
from cldfbench.cldf import CLDFWriter
import pandas as pd
from cldfbench_cariban_meta import Dataset
import json
import sys
from pycldf.sources import Source
import pybtex

meta = Dataset()
full = len(sys.argv) > 1

lg_records = {}
for lg in ["tri", "hix", "aka"]:
    records = pd.read_csv(f"data/{lg}_texts.csv", keep_default_na=False)
    records["Language_ID"] = lg
    if "Comment" in records.columns:
        records.drop(columns="Comment", inplace=True)
    if not full:
        annotations = pd.read_csv(f"data/{lg}_ann.csv", keep_default_na=False)
        custom_dict = {x: i for i, x in enumerate(list(records["ID"]))}
        df = annotations.sort_values(by=["ID"], key=lambda x: x.map(custom_dict))

        df = pd.merge(annotations, records, how="left", on="ID").fillna("")
        df["Discont_NP"] = df["Value"]
        df["Discont_NP"].replace("y", "more material", inplace=True)
        df = df[(df["Discont_NP"] != "n") | (df["Comment"] != "")]
        lg_records[lg] = df
    else:
        lg_records[lg] = records.fillna("")


found_refs = []


def collect_refs(s):
    if s != "":
        found_refs.append(s.split("[")[0])


with CLDFWriter(
    CLDFSpec(dir="data/cldf", module="Generic", metadata_fname="metadata.json")
) as writer:
    writer.cldf.add_component("ExampleTable")
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
    )
    if not full:
        writer.cldf.add_columns(
            "ExampleTable",
            {
                "name": "Discont_NP",
                "required": True,
                "dc:description": "Are there non-adjacent, co-referential noun phrases?",
                "datatype": "string",
            },
            {
                "name": "Syntactic_Role",
                "required": False,
                "dc:description": "Syntactic role of the 'NP'",
                "datatype": "string",
            },
        )
    writer.cldf.add_component("LanguageTable")
    for lg, df in lg_records.items():
        for col in [
            "Analyzed_Word",
            "Analyzed_Word_Morphemes",
            "Gloss",
            "Part_Of_Speech",
        ]:
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
            writer.objects["ExampleTable"].append(rec)
        writer.objects["LanguageTable"].append(meta.get_lg(lg))

    bib = pybtex.database.parse_file("data/car.bib", bib_format="bibtex")
    sources = [
        Source.from_entry(k, e) for k, e in bib.entries.items() if k in found_refs
    ]
    writer.cldf.add_sources(*sources)

    writer.write()
