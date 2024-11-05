import csv
import os

from preflibtools.instances import OrdinalInstance
from preflibtools.instances.dataset import write_info_file

IN_FOLDER = os.path.join("..", "..", "tmp", "polandelectionsclean")

info = {
    "name": "Poland Local Elections",
    "abb": "poland_local_elections",
    "tags": ["Election", "Politics"],
    "series": "00068",
    "publication_date": "2024-11-05",
    "description": """<p>This dataset collects voting data from recent Polish local elections. In 2014, in all cities with up to 100 000 inhabitants a first-past-the-post system was used. For this, all cities with up to 20 000/50 000/100 000 inhabitants where divided into 15/21/23 constituencies. The dataset consists of elections from 1317 cities (excluding ones with low vote length). In a file, each constituency is considered to be a voter, ranking the alternatives as in the election results of that constituency.</p><p>This dataset was donated by <a href="https://sites.google.com/view/niclas-boehmer/home">Niclas Boehmer</a>.</p>""",
    "citations": "Niclas Boehmer, Robert Bredereck, Piotr Faliszewski and Rolf Niedermeier. <em>A Quantitative and Qualitative Analysis of the Robustness of (Real-World) Election Winners</em>, 2022.",
    "studies": "",
    "files": []
}


OUT_FOLDER = os.path.join("..", "..", "datasets", f"{info['series']} - {info['abb']}")
os.makedirs(OUT_FOLDER, exist_ok=True)


def file_number(counter):
    res = str(counter)
    while len(res) < 8:
        res = "0" + res
    return res


territory_code = {}
with open(os.path.join("..", "..", "tmp", "TERC_Urzedowy_2024-11-05.csv"), encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter=";")
    for row in reader:
        code = row["WOJ"] + row["POW"] + row["GMI"]
        if code[0] == "0":
            code = code[1:]
        territory_code[code] = f'{row["NAZWA"]} ({row["NAZWA_DOD"]})'

file_counter = 1
for file in sorted(os.listdir(IN_FOLDER)):
    if file.endswith("soi"):
        instance = OrdinalInstance()
        with open(os.path.join(IN_FOLDER, file)) as f:
            lines = [l for l in f.readlines() if l]
            instance.parse_old(lines)
        # new_orders = []
        # new_multiplicities = {}
        # for order in instance.orders:
        #     new_order = []
        #     for indif_class in order:
        #         new_indif_class = []
        #         for a in indif_class:
        #             new_indif_class.append(a + 1)
        #         new_indif_class = tuple(new_indif_class)
        #         new_order.append(new_indif_class)
        #     new_order = tuple(new_order)
        #     new_orders.append(new_order)
        #     new_multiplicities[new_order] = instance.multiplicity[order]
        # instance.orders = new_orders
        # instance.multiplicity = new_multiplicities

        instance.recompute_cardinality_param()
        instance.data_type = "soi"
        instance.infer_type()
        new_file_name = f"{info['series']}-{file_number(file_counter)}.{instance.data_type}"
        instance.file_name = new_file_name
        file_title = territory_code[file.split("_")[0]]
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