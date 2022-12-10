import pandas as pd
from pylingdocs.preprocessing import postprocess
from pylingdocs.preprocessing import preprocess
from pylingdocs.preprocessing import render_markdown
from pylingdocs.output import HTML, GitHub
from pycldf import Dataset
import json


ds = Dataset.from_metadata("data/cldf/metadata.json")

df = pd.read_csv("data/dataset.csv", keep_default_na=False)

stats = json.load(open("data/stats.json"))

interv_dic = {
    "multiple": "more material",
    "PART": "Intervening particle",
    "Vi": "intervening verb",
    "POSTP": "intervening postposition",
    "n": "intervening non-referential noun",
    "adv": "intervening adverb",
    "ERG": "intervening ergative marker",
}

output = ["# Apparent discontinuous noun phrases"]

lgs = ["hix", "tri", "aka", "mak", "yab"]
for lg in lgs:
    discont = df[(df["Language_ID"] == lg) & (df["Discontinuous"] == "True")]
    if len(discont) == 0:
        continue
    output.append(f"## [lg]({lg})")
    for k, v in interv_dic.items():
        if k not in list(discont["Intervening"]):
            continue
        type_df = discont[discont["Intervening"] == k]
        for rec in type_df.to_dict("records"):
            output.append(f"""[ex]({rec["ID"]})""")


output.append("# Apparent noun phrases")
for lg in lgs:
    cont = df[(df["Language_ID"] == lg) & (df["Discontinuous"] == "False")]
    if len(cont) == 0:
        continue
    output.append(f"## [lg]({lg})")
    for kind in set(cont["Type"]):
        output.append(f"### {kind}")
        for rec in cont.to_dict("records"):
            if rec["Type"] != kind:
                continue
            output.append(f"""[ex]({rec["ID"]})""")

output.append("# Open questions")
for lg in lgs:
    cont = df[(df["Language_ID"] == lg) & (df["Value"] == "?")]
    if len(cont) == 0:
        continue
    output.append(f"## [lg]({lg})")
    for kind in set(cont["Type"]):
        for rec in cont.to_dict("records"):
            if rec["Type"] != kind:
                continue
            output.append(f"""* {rec["Comment"]}\n[ex]({rec["ID"]}?with_primaryText)""")


print(output)


# pos_overview = {}
# np_overview = {}
# res_overview = {}
# q_overview = {}
# arg_np_overview = {}
# dd_np_overview = {}


# stat_overview = []
# for lg, total in stats.items():
#     for d in [
#         pos_overview,
#         np_overview,
#         res_overview,
#         q_overview,
#         arg_np_overview,
#         dd_np_overview,
#     ]:
#         d[lg] = []
#     recs = df[df["Language_ID"] == lg]
#     positives = recs[recs["Discont_NP"].isin(["y", "part", "posp"])]
#     arg_nps = recs[(recs["Discont_NP"] == "np_arg")]
#     dd_nps = recs[(recs["Discont_NP"] == "np_dd")]
#     nps = recs[(recs["Discont_NP"] == "np")]
#     questions = recs[recs["Discont_NP"] == "?"]
#     residue = recs[
#         ~(
#             recs["ID"].isin(
#                 list(positives["ID"])
#                 + list(nps["ID"])
#                 + list(questions["ID"])
#                 + list(arg_nps["ID"])
#                 + list(dd_nps["ID"])
#             )
#         )
#     ]
#     assert len(positives) + len(nps) + len(questions) + len(residue) + len(
#         arg_nps
#     ) + len(dd_nps) == len(recs)
#     if len(positives) > 0:
#         df = pd.crosstab(
#             positives["Discont_NP"],
#             positives["Syntactic_Role"],
#             margins=True,
#             margins_name="Total",
#         )
#         df.index = df.index.map(label_dic)
#         df.index.name = "Pattern / Syntactic role"
#         stat_overview.append(
#             f"[lg]({lg}): {len(positives)}/{total} ({len(positives)/total:.2%}) text records with apparent discontinuous noun phrases:\n\n"
#             + df.to_markdown()
#         )
#     for o, t in [
#         (positives, pos_overview),
#         (questions, q_overview),
#         (residue, res_overview),
#         (arg_nps, arg_np_overview),
#         (dd_nps, dd_np_overview),
#         (nps, np_overview),
#     ]:
#         for rec in o.to_dict("records"):
#             comm_str = ""
#             if t not in [np_overview, arg_np_overview]:
#                 comm_str = comm_str = f"""* {label_dic[rec["Discont_NP"]]}"""
#                 if rec["Comment"] != "":
#                     comm_str += f""" ({rec["Comment"]})"""
#                 comm_str += ":\n"
#             else:
#                 if rec["Comment"] != "":
#                     comm_str += f"""{rec["Comment"]}:\n"""

#             t[lg].append(f"""{comm_str}[ex]({rec["ID"]}?with_primaryText)""")

# overview = []
# for title, dic in {
#     "Apparent discontinuous noun phrases": pos_overview,
#     "Putative NPs in argument position": arg_np_overview,
#     "Putative NPs with two demonstratives": dd_np_overview,
#     "Unclear analysis": q_overview,
#     "Varia": res_overview,
#     "Other putative NPs": np_overview,
# }.items():
#     overview.append(f"# {title}")
#     for lg, data in dic.items():
#         if len(data) == 0:
#             continue
#         overview.append(f"## [lg]({lg}): {title}")
#         overview.extend(data)


# content = "# Some stats\n" + "\n\n".join(stat_overview) + "\n\n" + "\n".join(overview)
builder = GitHub
preprocessed = preprocess("\n".join(output))
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
