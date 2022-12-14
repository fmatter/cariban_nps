import pandas as pd
import questionary
import re
from pathlib import Path
import json

lg_list = ["hix", "tri", "aka", "yab", "mak"]
# lg_list = ["yab"]
TARGET = 1000
LIMIT = 10


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
        [str(x + 1) for x in range(0, len(rec["Analyzed_Word"].split("\t")))],
    )
    surf = re.sub(r"\s+", " ", rec["Primary_Text"])
    print(f"""({rec.name}) {surf}\n{gloss_string}\nā{rec['Translated_Text']}ā\n""")


for lg in lg_list:
    print(lg)
    ann_path = Path(f"data/{lg}_ann.csv")
    if ann_path.is_file():
        info = pd.read_csv(ann_path)
    else:
        info = pd.DataFrame(
            columns=[
                "Example_ID",
                "Value",
                "Comment",
                "Pattern",
                "Positions",
                "Animacy",
                "Role",
                "Particle",
            ]
        )

    df = pd.read_csv(f"data/{lg}_data.csv")
    if "Comment" in df.columns:
        df.drop(columns=["Comment"], inplace=True)
    df = df.merge(info, left_on="ID", right_on="Example_ID", how="outer").fillna("")
    df = df.iloc[0:TARGET]

    df["Todo"] = df.apply(
        lambda x: (x["Pre_Screened"] != "y" and x["Value"] == ""), axis=1
    )

    eliminated = df[(df["Pre_Screened"] == "y") & (df["Value"] == "")]
    annotated = len(df[df["Value"] != ""])
    todo = len(df[df["Todo"]])
    print(len(eliminated), annotated, todo)
    eliminated[["ID"]].to_csv(f"data/{lg}_elim.csv", index=False)
    eliminated = len(eliminated)
    assert eliminated + annotated + todo == TARGET

    if annotated + todo > 0:
        print(
            f"{annotated} records done, {eliminated} pre-eliminated\n{annotated/(annotated+todo):.2%}, {todo} to go!"
        )
    with open("data/stats.json", "r") as f:
        stats = json.load(f)
        stats[lg] = annotated + eliminated
    with open("data/stats.json", "w") as f:
        json.dump(stats, f)

    answered = 0
    new_info = []
    searching_first_todo = True
    for i, rec in df.iterrows():
        if rec.name >= TARGET:
            continue
        if rec["Todo"]:
            searching_first_todo = False
        if searching_first_todo:
            continue
        if LIMIT and answered == LIMIT:
            continue
        print_record(rec)
        if rec["Todo"]:
            answered += 1
            choices = [
                "No",
                "Yes",
                "Just a comment",
                "It's complicated",
                "I want out",
            ]
            answer = questionary.rawselect("Any pseudo-NP?", choices=choices).ask()
            if answer == choices[0]:
                new_info.append({"Example_ID": rec["ID"], "Value": "n"})
            elif answer == choices[1]:
                pattern = questionary.text("Pattern?").ask()
                positions = questionary.text("Positions?").ask()
                role = questionary.text("Role?").ask()
                animacy = questionary.rawselect(
                    "Animacy?", choices=["hum", "anim", "inan"]
                ).ask()
                new_info.append(
                    {
                        "Example_ID": rec["ID"],
                        "Value": "y",
                        "Pattern": pattern,
                        "Positions": positions,
                        "Role": role,
                        "Animacy": animacy,
                    }
                )
            elif answer == choices[2]:
                comment = questionary.text("Comment?").ask()
                new_info.append(
                    {"Example_ID": rec["ID"], "Value": "n", "Comment": comment}
                )
            elif answer == choices[3]:
                comment = questionary.text("What's the problem?").ask()
                new_info.append(
                    {"Example_ID": rec["ID"], "Value": "?", "Comment": comment}
                )
            elif answer == choices[4]:
                break
            print(
                "----------------------------------------------------------------------------"
            )
    new_info = pd.DataFrame.from_dict(new_info)
    info = pd.concat([info, new_info]).fillna("")
    info.to_csv(f"data/{lg}_ann.csv", index=False)
