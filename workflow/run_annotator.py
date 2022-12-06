import pandas as pd
import questionary
import re
from pathlib import Path
import json

lg = "mak"
TARGET = 1000


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


def print_record(rec):
    gloss_string = pad_ex(
        rec["Analyzed_Word"].split("\t"),
        rec["Gloss"].split("\t"),
        rec["Part_Of_Speech"].split("\t"),
    )
    surf = re.sub(r"\s+", " ", rec["Primary_Text"])
    print(f"""({rec.name}) {surf}\n{gloss_string}\n‘{rec['Translated_Text']}’\n""")


ann_path = Path(f"data/{lg}_ann.csv")
if ann_path.is_file():
    info = pd.read_csv(ann_path)
else:
    info = pd.DataFrame(columns=["ID", "Value", "Comment", "Syntactic_Role"])


df = pd.read_csv(f"data/{lg}_texts.csv")

df = df.merge(info, on="ID", how="outer").fillna("")
df = df.iloc[0:TARGET]
df["Todo"] = df.apply(lambda x: (x["Pre_Screened"] != "y" and x["Value"] == ""), axis=1)
eliminated = len(df[(df["Pre_Screened"] == "y") & (df["Value"] == "")])
annotated = len(df[df["Value"] != ""])
todo = len(df[df["Todo"]])
assert eliminated + annotated + todo == TARGET

if annotated+todo > 0:
    print(
    f"{annotated} records done, {eliminated} pre-eliminated\n{annotated/(annotated+todo):.2%}, {todo} to go!"
)
with open("data/stats.json", "r") as f:
    stats = json.load(f)
    stats[lg] = annotated + eliminated
with open("data/stats.json", "w") as f:
    json.dump(stats, f)

new_info = []
searching_first_todo = True
for i, rec in df.iterrows():
    if rec.name >= TARGET:
        continue
    if rec["Todo"]:
        searching_first_todo = False
    if searching_first_todo:
        continue
    print_record(rec)
    if rec["Todo"]:
        choices = [
            "No",
            "Yes!",
            "Particle",
            "Postposition",
            "A nice 'NP'",
            "It's complicated",
            "I want out",
        ]
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
