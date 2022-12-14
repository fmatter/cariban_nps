import pandas as pd
import yaml
from pathlib import Path

lg_list = ["tri", "hix", "aka", "mak", "yab"]


def typify(rec):
    parts = rec["Order"].split(" ")
    if "DEM" in parts and "N" in parts:
        return "DEM+N"
    elif "N" in parts and "Nmod" in parts:
        return "Nmod+N"
    elif "ADV" in parts:
        return "ADV+N"
    elif "NUM" in parts:
        return "NUM+N"
    elif parts.count("N") > 1:
        return "N+N"
    elif parts == ["DEM", "DEM"]:
        return "DEM+DEM"
    else:
        raise ValueError(rec)

modifiers = ["ADV", "NUM", "Nmod", "DEM"]
mod_dict = {x: "mod" for x in modifiers}
mod_dict["N"] = "ref"
def abstractify(string):
    if string in ["N N", "DEM DEM"]:
        return "?"
    return " ".join([mod_dict[x] for x in string.split(" ")])

def resolve_pattern(rec):
    if rec["Pattern"] == "":
        return rec
    if not (
        rec["Pattern"].startswith("DEM")
        or rec["Pattern"].startswith("N")
        or rec["Pattern"].startswith("ADV")
        or rec["Pattern"].startswith("pro N")
    ):
        raise ValueError(rec)
    if (
        "POSTP" in rec["Pattern"]
        or "Vt" in rec["Pattern"]
        or rec["Role"] == "possr"
        or "ERG" in rec["Pattern"]
    ):
        rec["Argument"] = True
    else:
        rec["Argument"] = False
    discont_kind = ""
    discont = False
    elements = ["N", "DEM", "ADV", "NUM", "Nmod"]
    for pos in rec["Pattern"].split(" ")[1::]:
        if pos not in elements:
            discont = True
            if discont_kind == "":
                discont_kind = pos
            else:
                discont_kind += " " + pos
        else:
            break
    if rec["Pattern"] == "Nmod N Vt Nmod":
        discont_kind = "Vt"
        discont = True
    rec["Order"] = " ".join([x for x in rec["Pattern"].split(" ") if x in elements])
    rec["Abstract_Order"] = abstractify(rec["Order"])
    rec["Type"] = typify(rec)
    if " " in discont_kind:
        if discont_kind == "PART PART":
            discont_kind = "PART"
        else:
            discont_kind = "multiple"
    rec["Intervening"] = discont_kind
    if discont:
        if discont_kind == "PART":
            rec["Discontinuous"] = "Particle"
        else:
            rec["Discontinuous"] = "Yes"
    else:
        rec["Discontinuous"] = "No"
    return rec

split_cols = ["Analyzed_Word", "Gloss", "Part_Of_Speech"]
def add_brackets(rec):
    if rec["Constituents"] != "":
        starts = {}
        ends = {}
        for cons in rec["Constituents"].split(","):
            label, value = cons.split(":")
            if "-" in value:
                start, end = map(int, value.split("-"))
            else:
                start = int(value)
                end = int(value)
            starts[start] = label
            ends[end] = label 
        print(starts, ends)
        for col in split_cols:
            new_content = []
            for i, w in enumerate(rec[col].split("\t")):
                print("word", i, w)
                if i+1 in starts:
                    print("start", i)
                    if col == "Analyzed_Word":
                        new_content.append("[")
                    else:
                        new_content.append(" ")
                new_content.append(w)
                if i+1 in ends:
                    print("end", i)
                    if col == "Analyzed_Word":
                        new_content.append(f"]<sub>{ends[i+1]}</sub>")
                    else:
                        new_content.append(" ")
            rec[col] = "\t".join(new_content)
            print(rec[col])
        print(rec)
    return rec

repl_shorthand = {
    "trans": "Translated_Text",
    "gloss": "Gloss",
    "obj": "Analyzed_Word",
    "surf": "Primary_Text",
    "pos": "Part_Of_Speech",
}
with open("data/replace.yaml", "r") as f:
    repl = yaml.load(f, Loader=yaml.SafeLoader)

ex_cnt = {}


def get_ex_id(rec):
    if rec["Example_ID"] not in ex_cnt:
        ex_cnt[rec["Example_ID"]] = 0
        return rec["Example_ID"]
    else:
        ex_cnt[rec["Example_ID"]] += 1
        return rec["Example_ID"] + f"-{ex_cnt[rec['Example_ID']]}"


count_stats = []
dfs = []
full_dfs = []
for lg in lg_list:
    print(lg)
    data = pd.read_csv(f"data/{lg}_data.csv", keep_default_na=False, index_col=0)
    for ex_id, values in repl.items():
        if ex_id in data.index:
            for key, value in values.items():
                if key in ["obj", "gloss", "pos"]:
                    value = value.replace(" ", "\t")
                data.at[ex_id, repl_shorthand[key]] = value
    data.reset_index(inplace=True)
    ann = pd.read_csv(f"data/{lg}_ann.csv", keep_default_na=False)

    ann.reset_index(inplace=True)
    ann["ID"] = ann.apply(lambda x: get_ex_id(x), axis=1)
    texts = pd.read_csv(f"data/{lg}_texts.csv", keep_default_na=False)
    elim = pd.read_csv(f"data/{lg}_elim.csv", keep_default_na=False)
    full = data[data["ID"].isin(list(ann["Example_ID"]) + list(elim["ID"]))]
    full["Language_ID"] = lg
    full_dfs.append(full.copy())
    full = full.merge(
        texts, left_on="Text_ID", right_on="ID", how="left", suffixes=("", "_texts")
    )
    full["Word_Count"] = full["Analyzed_Word"].apply(lambda x: len(x.split("\t")))

    ann = ann.apply(lambda x: resolve_pattern(x), axis=1)

    noun_count = full["Noun_Count"].sum()
    word_count = full["Word_Count"].sum()

    full = ann.merge(
        full, left_on="Example_ID", right_on="ID", suffixes=("", "_corpus")
    )
    full = full[~((full["Pattern"] == "") & (full["Comment"] == ""))]

    discont_count = len(full[(full["Pattern"] != "") & (full["Discontinuous"] == "Yes")])
    pseudo_count = len(full[full["Pattern"] != ""])

    count_stats.append(
        {
            "Language": f"[lg]({lg})",
            "Words": word_count,
            "Nouns": noun_count,
            "Modified nouns": f"{pseudo_count} ({pseudo_count/noun_count:.2%})",
            "Discontinuous": f"{discont_count} ({discont_count/noun_count:.2%})",
        }
    )

    target_cols = [
        "ID",
        "Example_ID",
        "Language_ID",
        "Text_ID",
        "Original_Primary_Text",
        "Primary_Text",
        "Analyzed_Word",
        "Analyzed_Word_Morphemes",
        "Gloss",
        "Part_Of_Speech",
        "Constituents",
        "Original_Translated_Text",
        "Translated_Text",
        "Comment",
        "Pattern",
        "Discontinuous",
        "Intervening",
        "Animacy",
        "Type",
        "Order",
        "Abstract_Order",
        "Argument",
        "Role",
        "Positions",
        "Value",
        "Particle",
        "Genre",
        "Source",
    ]
    full = full[[x for x in target_cols if x in full.columns]]
    # print(full["Genre"].value_counts() / len(full))
    dfs.append(full)

full_df = pd.concat(full_dfs)
full_df.to_csv("data/full_data.csv", index=False)

df = pd.concat(dfs)

fix_cols = ["Analyzed_Word", "Gloss", "Part_Of_Speech"]
for col in fix_cols:
    df[col] = df[col].replace("\*\*\*", "???", regex=True)


def add_positions(rec):
    if rec["Positions"] != "":
        positions = [int(x) - 1 for x in rec["Positions"].split(",")]
        words = rec["Analyzed_Word"].split("\t")
        words = "\t".join(
            ["**" + x + "**" if i in positions else x for i, x in enumerate(words)]
        )
        rec["Analyzed_Word"] = words
    return rec


pc = df[(df["Intervening"] == "PART") & (df["Particle"] == "")]
if len(pc) > 0:
    print(pc)
tc = df[(df["Role"] != "p") & (df["Pattern"].str.contains("Vt"))]
if len(tc) > 0:
    print(tc)
oc = df[(df["Role"] != "obl") & (df["Pattern"].str.contains("POSTP"))]
if len(oc) > 0:
    print(oc)
temp = df[df["Pattern"] != ""]
dc = temp[(temp["Intervening"] == "") & (temp["Discontinuous"])]
if len(dc) > 0:
    print(dc)


TABLES = Path("docs/np-discont-slides/tables")


def save_table(df, name):
    df.to_csv(TABLES / f"{name}.csv", index=False)


count_df = pd.DataFrame.from_dict(count_stats)
save_table(count_df, "basic-counts")

df = df.apply(lambda x: add_positions(x), axis=1)
df = df.apply(lambda x: add_brackets(x), axis=1)

df.to_csv("data/dataset.csv", index=False)

# for k, type_df in df.groupby("Type"):
#     print(k)
#     print(type_df)
#     print(pd.crosstab(type_df["Order"], [type_df["Language_ID"]]))

# print(df[df["Order"] == "N N"])