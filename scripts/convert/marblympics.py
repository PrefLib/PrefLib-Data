import os

from preflibtools.instances import OrdinalInstance
from preflibtools.instances.dataset import write_info_file

IN_FOLDER = os.path.join("..", "..", "tmp", "marblympics")
OUT_FOLDER = os.path.join("..", "..", "datasets", "00065 - marblympics")

os.makedirs(OUT_FOLDER, exist_ok=True)

info = {
    "name": "Marble League (FKA Marble Olympics)",
    "abb": "marblympics",
    "tags": ["Sport"],
    "series": "00065",
    "publication_date": "2024-11-05",
    "description": """<p>The Marble League (formerly known as the MarbleLympics) is an annual tournament where marbles from different teams compete against each other in a number of different sports events (<a href="https://jellesmarbleruns.fandom.com/wiki/Marble_League">see here</a> for more details).<p>For each instance of the league, several events are organised that all lead to an intermediate ranking of the competitors. In the files, each event corresponds to a voter ranking the alternatives as they were ranked in the event.</p><p>This dataset was donated by <a href="https://sites.google.com/view/niclas-boehmer/home">Niclas Boehmer</a>.</p>""",
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
        file_title = f"Marble League {file[6:10]}"
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
