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

label_dic = {
    "part": "N Ptc N",
    "posp": "N Postp N",
    "y": "N [V...] N",
    "np_arg": "Pseudo-NP as an argument",
    "?": "unknown",
    "n": "other",
    "Total": "Total",
}
pos_overview = {}
np_overview = {}
res_overview = {}
q_overview = {}
arg_np_overview = {}

stat_overview = []
for lg, total in stats.items():
    for d in [pos_overview, np_overview, res_overview, q_overview, arg_np_overview]:
        d[lg] = []
    recs = all_recs[all_recs["Language_ID"] == lg]
    positives = recs[recs["Discont_NP"].isin(["y", "part", "posp"])]
    arg_nps = recs[(recs["Discont_NP"] == "np_arg")]
    nps = recs[(recs["Discont_NP"] == "np")]
    questions = recs[recs["Discont_NP"] == "?"]
    residue = recs[
        ~(
            recs["ID"].isin(
                list(positives["ID"])
                + list(nps["ID"])
                + list(questions["ID"])
                + list(arg_nps["ID"])
            )
        )
    ]
    assert len(positives) + len(nps) + len(questions) + len(residue) + len(
        arg_nps
    ) == len(recs)
    if len(positives) > 0:
        df = pd.crosstab(
            positives["Discont_NP"],
            positives["Syntactic_Role"],
            margins=True,
            margins_name="Total",
        )
        df.index = df.index.map(label_dic)
        df.index.name = "Pattern / Syntactic role"
        stat_overview.append(
            f"[lg]({lg}): {len(positives)}/{total} ({len(positives)/total:.2%}) text records with apparent discontinuous noun phrases:\n\n"
            + df.to_markdown()
        )
    for o, t in [
        (positives, pos_overview),
        (questions, q_overview),
        (residue, res_overview),
        (arg_nps, arg_np_overview),
        (nps, np_overview),
    ]:
        for rec in o.to_dict("records"):
            comm_str = ""
            if t not in [np_overview, arg_np_overview]:
                comm_str = comm_str = f"""* {label_dic[rec["Discont_NP"]]}"""
                if rec["Comment"] != "":
                    comm_str += f""" ({rec["Comment"]})"""
                comm_str += ":\n"
            else:
                if rec["Comment"] != "":
                    comm_str += f"""{rec["Comment"]}:\n"""

            t[lg].append(f"""{comm_str}[ex]({rec["ID"]}?with_primaryText)""")

overview = []
for title, dic in {
    "Apparent discontinuous noun phrases": pos_overview,
    "Putative NPs in argument position": arg_np_overview,
    "Unclear analysis": q_overview,
    "Varia": res_overview,
    "Other putative NPs": np_overview,
}.items():
    overview.append(f"# {title}")
    for lg, data in dic.items():
        if len(data) == 0:
            continue
        overview.append(f"## [lg]({lg}): {title}")
        overview.extend(data)

builder = GitHub
content = "# Some stats\n" + "\n\n".join(stat_overview) + "\n\n" + "\n".join(overview)

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
