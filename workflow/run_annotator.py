import pandas as pd
import questionary
import re
from pathlib import Path


def pad_ex(*lines, sep=" "):
    out = {}
    for glossbundle in zip(*lines):
        longest = len(max(glossbundle, key=len))
        for i, obj in enumerate(glossbundle):
            diff = longest - len(obj)
            out.setdefault(i, [])
            out[i].append(obj + " " * diff)
    for k in out:
        out[k] = sep.join(out[k])
    return "\n".join(out.values())


lg = "tri"


def print_record(rec):
    gloss_string = pad_ex(
        rec["Analyzed_Word"].split("\t"),
        rec["Gloss"].split("\t"),
        rec["Part_Of_Speech"].split("\t"),
    )
    surf = re.sub(r"\s+", " ", rec["Primary_Text"])
    print(f"""({rec.name}) {surf}\n{gloss_string}\n{rec['Translated_Text']}\n""")


ann_path = Path(f"data/{lg}_ann.csv")
if ann_path.is_file():
    info = pd.read_csv(ann_path)
else:
    info = pd.DataFrame(columns=["ID", "Value", "Comment"])


df = pd.read_csv(f"data/{lg}_texts.csv", keep_default_na=False)


def screen_rec(rec):
    if rec["Part_Of_Speech"].count("N") > 1:
        return True
    if rec["Part_Of_Speech"].count("N") >= 1 & rec["Part_Of_Speech"].count("DPro") >= 1:
        return True
    return False

unannotated = df[~(df["ID"].isin(info["ID"]))]
unannotated["Candidate"] = unannotated.apply(lambda x: screen_rec(x), axis=1)

w_c = sum(df[(df["ID"].isin(info["ID"]))]["Analyzed_Word"].apply(lambda x: x.count("\t") + 1))
pre_elim = len(info[info["Pre_Screened"] == "y"])
total_disc_count = info["Value"].value_counts().get("y", 0)
print(
    f"{len(info)} records done ({len(info)/10:.1f}%, {pre_elim} pre-eliminated)\n{w_c} words; {total_disc_count} discontinuous noun phrases\n"
)

new_info = []
for i, rec in unannotated.iterrows():
    if rec.name > 999:
        continue
    print_record(rec)
    if not rec["Candidate"]:
        new_info.append({"ID": rec["ID"], "Value": "n", "Pre_Screened": "y"})
    else:
        choices = ["No", "Yes!", "Particle", "Postposition", "A nice 'NP'", "It's complicated", "I want out"]
        answer = questionary.rawselect("Any discontinuous NP?", choices=choices).ask()
        if answer == choices[0]:
            new_info.append({"ID": rec["ID"], "Value": "n"})
        elif answer == choices[1]:
            new_info.append({"ID": rec["ID"], "Value": "y"})
        elif answer == choices[2]:
            new_info.append({"ID": rec["ID"], "Value": "part"})
        elif answer == choices[3]:
            new_info.append({"ID": rec["ID"], "Value": "posp"})
        elif answer == choices[4]:
            new_info.append({"ID": rec["ID"], "Value": "np"})
        elif answer == choices[5]:
            comment = questionary.text("What's the problem?").ask()
            if " / " in comment:
                comment, value = comment.split(" / ")
            else:
                value = "?"
            new_info.append({"ID": rec["ID"], "Value": value, "Comment": comment})
        elif answer == choices[6]:
            break
        print(
            "----------------------------------------------------------------------------"
        )
new_info = pd.DataFrame.from_dict(new_info)
info = pd.concat([info, new_info]).fillna("")
info.to_csv(f"data/{lg}_ann.csv", index=False)
