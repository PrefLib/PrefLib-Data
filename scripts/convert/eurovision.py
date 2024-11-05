import os

from preflibtools.instances import OrdinalInstance
from preflibtools.instances.dataset import write_info_file

IN_FOLDER = os.path.join("..", "..", "tmp", "eurovision")
OUT_FOLDER = os.path.join("..", "..", "datasets", "00064 - eurovision")

os.makedirs(OUT_FOLDER, exist_ok=True)

info = {
    "name": "Eurovision Song Contest",
    "abb": "eurovision",
    "tags": ["Election"],
    "series": "00064",
    "publication_date": "2024-11-05",
    "description": """<p>This dataset collects the vote from the European Song Contest. Every candidate is a country (resp. their representative singer) and every vote is also a country. In the original format they only organised a final, from 2004 onwards semi-finals were added.</p><p>This dataset was donated by <a href="https://sites.google.com/view/niclas-boehmer/home">Niclas Boehmer</a>.</p>""",
    "citations": "Niclas Boehmer. <em>Application-oriented Collective Decision Making: Experimental Toolbox and Dynamic Environments</em>, 2023.",
    "studies": "",
    "files": []
}


def file_number(counter):
    res = str(counter)
    while len(res) < 8:
        res = "0" + res
    return res


file_counter = 1
for file in sorted(os.listdir(IN_FOLDER)):
    if file.endswith("soi"):
        instance = OrdinalInstance()
        with open(os.path.join(IN_FOLDER, file)) as f:
            lines = [l for l in f.readlines() if l]
            instance.parse_old(lines)
        instance.recompute_cardinality_param()
        instance.data_type = "soi"
        instance.infer_type()
        new_file_name = f"{info['series']}-{file_number(file_counter)}.{instance.data_type}"
        instance.file_name = new_file_name
        title_suffix = ""
        if file.split("_")[0][4:] == "f":
            title_suffix = "Final"
        elif file.split("_")[0][4:] == "sf1":
            title_suffix = "Semi-Final 1"
        elif file.split("_")[0][4:] == "sf2":
            title_suffix = "Semi-Final 2"
        elif file.split("_")[0][4:] == "sf":
            title_suffix = "Semi-Final"
        file_title = f"ESC {file[:4]} - {title_suffix}"
        instance.title = file_title
        instance.modification_type = "original"
        instance.publication_date = info["publication_date"]
        instance.modification_date = instance.publication_date
        info["files"].append({
            "file_name": instance.file_name,
            "modification_type": instance.modification_type,
            "relates_to": instance.relates_to,
            "title": instance.title,
            "description": instance.description,
            "publication_date": instance.publication_date
        })
        instance.write(os.path.join(OUT_FOLDER, new_file_name))

        file_counter += 1

write_info_file(os.path.join(OUT_FOLDER, "info.txt"), info)
