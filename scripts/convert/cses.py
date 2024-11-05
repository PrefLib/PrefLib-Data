import os

from preflibtools.instances import OrdinalInstance
from preflibtools.instances.dataset import write_info_file
import pycountry

IN_FOLDERS = [
    os.path.join("..", "..", "tmp", "CSES_leaders_national"),
    os.path.join("..", "..", "tmp", "CSES_parties_national"),
]

info = {
    "name": "Comparative Study of Electoral Systems",
    "abb": "cses",
    "tags": ["Election", "Politics"],
    "series": "00067",
    "publication_date": "2024-11-05",
    "description": """<p>This dataset presents data collected as part of the Comparative Study of Electoral Systems. This study consists of post-election studies from (federal) elections from different countries. In some of these post-election studies, participants were asked to rank all important political parties or leaders in their country that they know on a scale from 0 to 10 according to how much they agree with the views of the party. For each of the 174 post-election studies where this question was asked, we form an election with the parties as candidates. Each voter in this election then corresponds to a participant in the survey and ranks the parties according to the participant's answer. Check the <a href="https://cses.org/">website of the CSES</a> for more details.</p><p>This dataset was donated by <a href="https://sites.google.com/view/niclas-boehmer/home">Niclas Boehmer</a>.</p>""",
    "citations": "The Comparative Study of Electoral Systems. <em>CSES module 1 full release</em>, 2015. | The Comparative Study of Electoral Systems. <em>CSES module 2 full release</em>, 2015. | The Comparative Study of Electoral Systems. <em>CSES module 3 full release</em>, 2015. | The Comparative Study of Electoral Systems. <em>CSES module 4 full release</em>, 2018. | The Comparative Study of Electoral Systems. <em>CSES module 5 full release</em>, 2022.",
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


def get_country_name(country_code):
    try:
        country = pycountry.countries.get(alpha_3=country_code)
        return country.name if country else "Unknown Country"
    except KeyError:
        return "Unknown Country"


def construct_file_title(file_path):
    old_file_name = os.path.basename(file_path)
    if old_file_name == "BELF1999.soc":
        file_title = "Belgium (Flanders) 1999"
    elif old_file_name == "BELW1999.soc":
        file_title = "Belgium (Wallonia) 1999"
    elif old_file_name == "DEU12002.soc":
        file_title = "Germany 2002A"
    elif old_file_name == "DEU22002.soc":
        file_title = "Germany 2002B"
    else:
        country_code = old_file_name.split('_')[0]
        file_title = f"{get_country_name(country_code)} {old_file_name.split('_')[1].split('.')[0]}"
    if all_files[file_path].endswith("L"):
        file_title += " - Leaders"
    else:
        file_title += " - Parties"
    return file_title


file_counter = 1
all_files = {}
for IN_FOLDER in IN_FOLDERS:
    for file in sorted(os.listdir(IN_FOLDER)):
        if "CSES_leaders_national" in IN_FOLDER:
            all_files[os.path.join(IN_FOLDER, file)] = file + " L"
        else:
            all_files[os.path.join(IN_FOLDER, file)] = file + " P"

for file_path in sorted(all_files, key=construct_file_title):
    if file_path[-3:] in ["soi", "soc", "toi", "toc"] and not "core_0.soc" in file_path:
        print(file_path)
        instance = OrdinalInstance()
        with open(file_path) as f:
            lines = [l for l in f.readlines() if l]
            instance.parse_old(lines[1:])

        new_orders = []
        new_multiplicities = {}
        for order in instance.orders:
            new_order = []
            for indif_class in order:
                new_indif_class = []
                for a in indif_class:
                    new_indif_class.append(a + 1)
                new_indif_class = tuple(new_indif_class)
                new_order.append(new_indif_class)
            new_order = tuple(new_order)
            new_orders.append(new_order)
            new_multiplicities[new_order] = instance.multiplicity[order]
        instance.orders = new_orders
        instance.multiplicity = new_multiplicities

        instance.recompute_cardinality_param()
        instance.data_type = "soi"
        instance.infer_type()
        new_file_name = f"{info['series']}-{file_number(file_counter)}.{instance.data_type}"
        instance.file_name = new_file_name
        instance.title = construct_file_title(file_path)
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
