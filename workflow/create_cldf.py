from cldfbench import CLDFSpec
from cldfbench.cldf import CLDFWriter
import pandas as pd
from cldfbench_cariban_meta import Dataset
import json

meta = Dataset()

lg_records = {}
total_ann = {}
for lg in ["tri", "hix"]:
    records = pd.read_csv(f"data/{lg}_texts.csv", keep_default_na=False)
    records["Language_ID"] = lg
    annotations = pd.read_csv(f"data/{lg}_ann.csv", keep_default_na=False)
    total_ann[lg] = len(annotations)
    annotations = annotations[
        (annotations["Value"] == "y") | (annotations["Comment"] != "")
    ]
    lg_records[lg] = pd.merge(records, annotations, how="right").fillna("")
    lg_records[lg]["Discont_NP"] = lg_records[lg]["Value"]

with open("data/stats.json", "w") as f:
    json.dump(total_ann, f)

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
            df[col] = df[col].apply(lambda x: x.split("\t"))
            df[col] = df[col].apply(lambda x: [y if y else "…" for y  in x])
        for rec in df.to_dict("records"):
            writer.objects["ExampleTable"].append(rec)
        writer.objects["LanguageTable"].append(meta.get_lg(lg))
    writer.write()
