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

    for dataset_dir in sorted(os.listdir(IN_DIR)):
        print(f"Reading {dataset_dir}")
        ds_files = []
        for datafile_name in os.listdir(os.path.join(IN_DIR, dataset_dir)):
            file_path = os.path.join(IN_DIR, dataset_dir, datafile_name)
            ds_files.append(file_path)
            data_type = datafile_name[:-3]
            if data_type in relevant_data_types:
                type_to_files[data_type].append(file_path)
                instance = get_parsed_instance(file_path)
                modif_to_files[instance.modification_type].append(file_path)
        dataset_to_files[dataset_dir] = ds_files

    for dataset, all_files in dataset_to_files.items():
        print(f"Zipping {dataset}")
        with zipfile.ZipFile(os.path.join(OUT_DIR, dataset.replace(" - ", "_") + ".zip"), "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in all_files:
                zip_file.write(file_path, os.path.basename(file_path))

    for modif_type, all_files in modif_to_files.items():
        print(f"Zipping {modif_type}")
        with zipfile.ZipFile(os.path.join(OUT_DIR, "modif_" + modif_type + ".zip"), "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in all_files:
                zip_file.write(file_path, os.path.basename(file_path))

    for data_type, all_files in type_to_files.items():
        print(f"Zipping {data_type}")
        with zipfile.ZipFile(os.path.join(OUT_DIR, "type_" + data_type + ".zip"), "w",
                             zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in all_files:
                zip_file.write(file_path, os.path.basename(file_path))


if __name__ == "__main__":
    zip_all()
