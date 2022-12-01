import pandas as pd
from pylingdocs.preprocessing import postprocess
from pylingdocs.preprocessing import preprocess
from pylingdocs.preprocessing import render_markdown
from pylingdocs.output import HTML, GitHub
from pycldf import Dataset
import json

ds = Dataset.from_metadata("data/cldf/metadata.json")

all_recs = pd.read_csv("data/cldf/examples.csv", keep_default_na=False)

stats = json.load(open("data/stats.json"))

pos_overview = {}
np_overview = {}
res_overview = {}
q_overview = {}

stat_overview = []
for lg, total in stats.items():
    for d in [pos_overview, np_overview, res_overview, q_overview]:
        d[lg] = []
    recs = all_recs[all_recs["Language_ID"] == lg]
    positives = recs[recs["Discont_NP"].isin(["more material", "part", "posp"])]
    nps = recs[(recs["Discont_NP"] == "np")]
    questions = recs[recs["Discont_NP"] == "?"]
    residue = recs[
        ~(
            recs["ID"].isin(
                list(positives["ID"]) + list(nps["ID"]) + list(questions["ID"])
            )
        )
    ]
    assert len(positives) + len(nps) + len(questions) + len(residue) == len(recs)
    if len(positives) > 0:
        df = pd.crosstab(
            positives["Discont_NP"], positives["Syntactic_Role"], margins=True
        )
        df.index.name = ""
        stat_overview.append(
            f"[lg]({lg}): {len(positives)}/{total} ({len(positives)/total:.2%}) text records with positive tokens:\n\n"
            + df.to_markdown()
        )
    for o, t in [
        (positives, pos_overview),
        (questions, q_overview),
        (residue, res_overview),
        (nps, np_overview),
    ]:
        for rec in o.to_dict("records"):
            comm_str = ""
            if rec["Comment"] != "" and t is not np_overview:
                comm_str = f"""* {rec["Discont_NP"]} ({rec["Comment"]}):\n"""
            t[lg].append(f"""{comm_str}[ex]({rec["ID"]}?with_primaryText)""")

overview = []
for title, dic in {
    "Positives": pos_overview,
    "Unclear": q_overview,
    "Others": res_overview,
    "NPs": np_overview,
}.items():
    overview.append(f"# {title}")
    for lg, data in dic.items():
        if len(data) == 0:
            continue
        overview.append(f"## [lg]({lg})")
        overview.extend(data)

builder = GitHub
content = "\n\n".join(stat_overview) + "\n".join(overview)
preprocessed = preprocess(content)
preprocessed = builder.preprocess_commands(preprocessed)
preprocessed += "\n\n" + builder.reference_list()
try:
    preprocessed = render_markdown(preprocessed, ds, output_format=builder.name)
except KeyError as e:
    print(f"Key not found: {e.args[0]}")
preprocessed = postprocess(preprocessed, builder)
builder.write_folder(
    output_dir=".",
    content=preprocessed,
    metadata={
        "title": "Overview of results",
        "version": "0.0.1",
        "author": "Florian Matter",
    },
)
