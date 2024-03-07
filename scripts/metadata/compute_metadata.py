import os
from multiprocessing import Pool

import pandas as pd

from preflibtools.instances import get_parsed_instance
from preflibtools.instances.dataset import read_info_file
from preflibtools.properties import num_alternatives, num_voters, num_different_preferences, \
    is_strict, is_complete, is_approval, is_single_peaked, is_single_crossing, largest_ballot, \
    smallest_ballot, max_num_indif, min_num_indif, largest_indif, smallest_indif, has_condorcet, \
    is_single_peaked_ILP


all_orders = ("soc", "soi", "toc", "toi")
all_orders_and_cat = ("soc", "soi", "toc", "toi", "cat")
METADATAS = {
    "file": {"appliesTo": None, "function": lambda x: x.file_name},
    "numAlt": {"appliesTo": None, "function": num_alternatives},
    "numVot": {"appliesTo": None, "function": num_voters},
    "numUniq": {"appliesTo": all_orders_and_cat, "function": num_different_preferences},
    "isStrict": {"appliesTo": all_orders, "function": is_strict},
    "isComplete": {"appliesTo": all_orders_and_cat, "function": is_complete},
    "isApproval": {"appliesTo": all_orders_and_cat, "function": is_approval},
    "largestBallot": {"appliesTo": all_orders_and_cat, "function": largest_ballot},
    "smallestBallot": {"appliesTo": all_orders_and_cat, "function": smallest_ballot},
    "maxNumIndif": {"appliesTo": all_orders_and_cat, "function": max_num_indif},
    "minNumIndif": {"appliesTo": all_orders_and_cat, "function": min_num_indif},
    "largestIndif": {"appliesTo": all_orders_and_cat, "function": largest_indif},
    "smallestIndif": {"appliesTo": all_orders_and_cat, "function": smallest_indif},
    "hasCondorcet": {"appliesTo": all_orders, "function": has_condorcet},
    "isSP": {"appliesTo": ("soc_aaaa", "toc_aaaa"), "function": {
        "soc": lambda x: is_single_peaked(x)[0],
        "toc": lambda x: is_single_peaked_ILP(x)[0]}},
    "isSC": {"appliesTo": ("soc_aaaa",), "function": is_single_crossing},
}
HEADERS = list(METADATAS)


def compute_file_metadata(file_path):
    if file_path[-3:] not in ("soc", "soi", "toc", "toi", "cat", "wmd"):
        return None
    file_name = os.path.basename(file_path)
    print(f"\t{file_name}")
    instance = get_parsed_instance(file_path)
    results = {}
    for meta, meta_info in METADATAS.items():
        if meta_info["appliesTo"] is None or instance.data_type in meta_info["appliesTo"]:
            func = meta_info["function"]
            if isinstance(func, dict):
                results[meta] = func[instance.data_type](instance)
            else:
                results[meta] = func(instance)
    return results


def compute_dataset_metadata(root_dir_path):
    print(f"Computing for {root_dir_path}")
    info = read_info_file(os.path.join(root_dir_path, "info.txt"))
    out_file_path = os.path.join(root_dir_path, "metadata.csv")
    with open(out_file_path, "w") as out_file:
        out_file.write(";".join(HEADERS) + "\n")

    # for file in info["files"]:
    #     metadata = compute_file_metadata(os.path.join(root_dir_path, file))
    #     if metadata is not None:
    #         with open(out_file_path, "a") as out_file:
    #             meta_write = [str(metadata[h]) if h in metadata else "N/A" for h in HEADERS]
    #             out_file.write(";".join(meta_write) + "\n")

    file_pool = Pool()
    files = []
    for file in info["files"]:
        files.append(os.path.join(root_dir_path, file))

    for metadata in file_pool.imap_unordered(compute_file_metadata, files):
        if metadata is not None:
            with open(out_file_path, "a") as out_file:
                meta_write = [str(metadata[h]) if h in metadata else "N/A" for h in HEADERS]
                out_file.write(";".join(meta_write) + "\n")


def read_all_metadata_files(root_dir_path):
    all_metadata = {}
    for ds_dir in os.listdir(root_dir_path):
        metadata = None
        try:
            metadata = pd.read_csv(
                os.path.join(root_dir_path, ds_dir, "metadata.csv"),
                delimiter=";",
                encoding="utf-8"
            )
        except FileNotFoundError:
            print(f"Could not find a metadata file for dataset {ds_dir}...")
        if metadata is not None:
            all_metadata[ds_dir] = metadata
    return all_metadata


def write_all_metadata_files(all_metadata, root_dir_path):
    for ds_dir, metadata in all_metadata.items():
        metadata.to_csv(
            os.path.join(root_dir_path, ds_dir, "metadata.csv"),
            delimiter=";",
            encoding="utf-8"
        )


DATASET_FOLDER = os.path.join("..", "..", "datasets")

if __name__ == '__main__':
    datasets = [os.path.join(DATASET_FOLDER, ds_dir) for ds_dir in os.listdir(DATASET_FOLDER)]

    all_meta = read_all_metadata_files(DATASET_FOLDER)
    # print(all_meta)

    # for ds in datasets:
    #     compute_dataset_metadata(ds)

    # pool = Pool()
    # for _ in pool.imap_unordered(compute_dataset_metadata, datasets):
    #     pass

