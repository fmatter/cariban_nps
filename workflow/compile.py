import pandas as pd

# lg_list = ["aka", "hix", "tri", "mak"]
lg_list = ["tri", "hix", "aka", "mak", "yab"]


def typify(rec):
    string = rec["Order"]
    if "DEM" in string and "N" in string:
        return "DEM+N"
    elif string.count("N") > 1:
        return "N+N"
    elif "ADV" in string:
        return "ADV+N"
    elif "NUM" in string:
        return "NUM+N"
    elif string == "DEM DEM":
        return "DEM+DEM"
    else:
        raise ValueError(rec)


def resolve_pattern(rec):
    if rec["Pattern"] == "":
        return rec
    if not (
        rec["Pattern"].startswith("DEM")
        or rec["Pattern"].startswith("N")
        or rec["Pattern"].startswith("ADV")
    ):
        raise ValueError(rec)
    if "POSP" in rec["Pattern"] or "Vt" in rec["Pattern"] or rec["Role"] == "possr" or "ERG" in rec["Pattern"]:
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
    rec["Order"] = " ".join([x for x in rec["Pattern"].split(" ") if x in elements])
    rec["Type"] = typify(rec)
    if " " in discont_kind:
        discont_kind = "multiple"
    rec["Intervening"] = discont_kind
    rec["Discontinuous"] = discont
    return rec


ex_cnt = {}
def get_ex_id(rec):
    if rec["Example_ID"] not in ex_cnt:
        ex_cnt[rec["Example_ID"]] = 0
        return rec["Example_ID"]
    else:
        ex_cnt[rec["Example_ID"]] += 1
        return rec["Example_ID"] + f"-{ex_cnt[rec['Example_ID']]}"

dfs = []
for lg in lg_list:
    print(lg)
    data = pd.read_csv(f"data/{lg}_data.csv", keep_default_na=False)
    ann = pd.read_csv(f"data/{lg}_ann.csv", keep_default_na=False)

    ann.reset_index(inplace=True)
    ann["ID"] = ann.apply(lambda x: get_ex_id(x), axis=1)
    texts = pd.read_csv(f"data/{lg}_texts.csv", keep_default_na=False)
    elim = pd.read_csv(f"data/{lg}_elim.csv", keep_default_na=False)
    full = data[data["ID"].isin(list(ann["Example_ID"]) + list(elim["ID"]))]
    full = full.merge(
        texts, left_on="Text_ID", right_on="ID", how="left", suffixes=("", "_texts")
    )
    full["Language_ID"] = lg
    full["Word_Count"] = full["Analyzed_Word"].apply(lambda x: len(x.split("\t")))

    ann = ann.apply(lambda x: resolve_pattern(x), axis=1)

    full = ann.merge(
        full, left_on="Example_ID", right_on="ID", suffixes=("", "_corpus")
    )
    full = full[~((full["Pattern"] == "") & (full["Comment"] == ""))]

    print(len(full[full["Pattern"] != ""]))
    print(len(full[full["Pattern"] != ""]) / full["Noun_Count"].sum())

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
        "Original_Translated_Text",
        "Translated_Text",
        "Comment",
        "Pattern",
        "Discontinuous",
        "Intervening",
        "Animacy",
        "Type",
        "Order",
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

df = pd.concat(dfs)


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

df = df.apply(lambda x: add_positions(x), axis=1)
# print(df)
print(pd.crosstab(df["Order"], [df["Language_ID"]]))
df.to_csv("data/dataset.csv", index=False)
