import csv
import zipfile
import os

from preflibtools.instances import get_parsed_instance

IN_DIR = os.path.join("..", "datasets")
OUT_DIR = os.path.join("..", "zip")
os.makedirs(OUT_DIR, exist_ok=True)


def zip_all():
    relevant_data_types = ("toc", "toi", "soc", "soi", "cat", "wmd")
    type_to_files = {t: [] for t in relevant_data_types}
    relevant_modif_types = ("imbued", "induced", "original", "synthetic")
    modif_to_files = {t: [] for t in relevant_modif_types}
    dataset_to_files = dict()
    relevant_properties = ("isApproval", "isStrict", "isComplete", "isSP", "isSC", "isSPTree")
    prop_to_files = {t: [] for t in relevant_properties}

    for dataset_dir in sorted(os.listdir(IN_DIR), reverse=True):
        print(f"Reading {dataset_dir}")
        ds_files = []

        file_to_metadatas = dict()
        with open(os.path.join(IN_DIR, dataset_dir, "metadata.csv"), encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                file_to_metadatas[row["file"]] = row

        for datafile_name in sorted(os.listdir(os.path.join(IN_DIR, dataset_dir))):
            print(f"\t.. {datafile_name}")
            file_path = os.path.join(IN_DIR, dataset_dir, datafile_name)
            ds_files.append(file_path)
            data_type = datafile_name[-3:]
            if data_type in relevant_data_types:
                type_to_files[data_type].append(file_path)
                metadata = file_to_metadatas[os.path.basename(file_path)]
                modif_to_files[metadata["modification_type"]].append(file_path)
                for prop in relevant_properties:
                    if metadata[prop] == "True":
                        prop_to_files[prop].append(file_path)
        dataset_to_files[dataset_dir] = ds_files

    type_to_files["toi"] += type_to_files["toc"] + type_to_files["soi"] + type_to_files["soc"]
    type_to_files["toc"] += type_to_files["soc"]
    type_to_files["soi"] += type_to_files["soc"]

    for dataset, all_files in dataset_to_files.items():
        print(f"Zipping {dataset}")
        with zipfile.ZipFile(os.path.join(OUT_DIR, dataset.replace(" - ", "_") + ".zip"), "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in all_files:
                zip_file.write(file_path, os.path.basename(file_path))
    #
    # for modif_type, all_files in modif_to_files.items():
    #     print(f"Zipping {modif_type}")
    #     with zipfile.ZipFile(os.path.join(OUT_DIR, "modif_" + modif_type + ".zip"), "w", zipfile.ZIP_DEFLATED) as zip_file:
    #         for file_path in all_files:
    #             zip_file.write(file_path, os.path.basename(file_path))
    #
    # for data_type, all_files in type_to_files.items():
    #     print(f"Zipping {data_type}")
    #     with zipfile.ZipFile(os.path.join(OUT_DIR, "type_" + data_type + ".zip"), "w",
    #                          zipfile.ZIP_DEFLATED) as zip_file:
    #         for file_path in all_files:
    #             zip_file.write(file_path, os.path.basename(file_path))
    #
    # for prop, all_files in prop_to_files.items():
    #     print(f"Zipping {prop}")
    #     with zipfile.ZipFile(os.path.join(OUT_DIR, "prop_" + prop + ".zip"), "w",
    #                          zipfile.ZIP_DEFLATED) as zip_file:
    #         for file_path in all_files:
    #             zip_file.write(file_path, os.path.basename(file_path))


if __name__ == "__main__":
    zip_all()
