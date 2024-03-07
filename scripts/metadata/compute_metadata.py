import os
from multiprocessing import Pool

import pandas as pd

from preflibtools.instances import get_parsed_instance
from preflibtools.instances.dataset import read_info_file
from preflibtools.properties import num_alternatives, num_voters, num_different_preferences, \
    is_strict, is_complete, is_approval, is_single_peaked, is_single_crossing, largest_ballot, \
    smallest_ballot, max_num_indif, min_num_indif, largest_indif, smallest_indif, has_condorcet, \
    is_single_peaked_ILP


class Property:
    def __init__(self, name, applies_to, func):
        self.name = name
        self.applies_to = applies_to
        self.func = func

    def applies_to_instance(self, instance):
        return self.applies_to is None or instance.data_type in self.applies_to

    def applies_to_file(self, file):
        return self.applies_to is None or os.path.splitext(file)[1][1:] in self.applies_to

    def compute_instance(self, instance):
        if self.applies_to_instance(instance):
            if isinstance(self.func, dict):
                return self.func[instance.data_type](instance)
            else:
                return self.func(instance)


def compute_file_properties(file_path, all_properties):
    if file_path[-3:] not in ("soc", "soi", "toc", "toi", "cat", "wmd"):
        return None
    file_name = os.path.basename(file_path)
    print(f"\t{file_name}")
    instance = get_parsed_instance(file_path)
    results = {}
    for prop in all_properties:
        res = prop.compute_instance(instance)
        if res is not None:
            results[prop.name] = res
    return results


def compute_dataset_metadata(root_dir_path):
    print(f"Computing for {root_dir_path}")
    info = read_info_file(os.path.join(root_dir_path, "info.txt"))
    out_file_path = os.path.join(root_dir_path, "metadata.csv")
    with open(out_file_path, "w") as out_file:
        out_file.write(";".join(HEADERS) + "\n")

    # for file in info["files"]:
    #     metadata = compute_file_properties(os.path.join(root_dir_path, file))
    #     if metadata is not None:
    #         with open(out_file_path, "a") as out_file:
    #             meta_write = [str(metadata[h]) if h in metadata else "N/A" for h in HEADERS]
    #             out_file.write(";".join(meta_write) + "\n")

    file_pool = Pool()
    files = []
    for file in info["files"]:
        files.append(os.path.join(root_dir_path, file))

    for metadata in file_pool.imap_unordered(compute_file_properties, files):
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
            sep=";",
            na_rep="N/A",
            index=False,
            encoding="utf-8",
        )
        print(f"Wrote the metadata file for {ds_dir}.")


def add_property_value(all_metadata, root_dir_path, property_obj):
    def apply_on_instance(df_row):
        file = df_row["file"]
        if property_obj.applies_to_file(file):
            instance = get_parsed_instance(os.path.join(root_dir_path, ds_dir, file))
            return property_obj.compute_instance(instance)

    print(f"Computing {property_obj.name} for datasets:")
    for ds_dir, metadata in all_metadata.items():
        print(f"\t{ds_dir} with {len(metadata)} files")
        if len(metadata) > 0:
            metadata[property_obj.name] = metadata.apply(apply_on_instance, axis=1)
        break


all_orders = ("soc", "soi", "toc", "toi")
all_orders_and_cat = ("soc", "soi", "toc", "toi", "cat")
ALL_PROPERTIES = [
    Property("file", None, lambda x: x.file_name),
    Property("numAlt", None, num_alternatives),
    Property("numVot", None, num_voters),
    Property("numUniq", all_orders_and_cat, num_different_preferences),
    Property("isStrict", all_orders, is_strict),
    Property("isComplete", all_orders_and_cat, is_complete),
    Property("isApproval", all_orders_and_cat, is_approval),
    Property("largestBallot", all_orders_and_cat, largest_ballot),
    Property("smallestBallot", all_orders_and_cat, smallest_ballot),
    Property("maxNumIndif", all_orders_and_cat, max_num_indif),
    Property("minNumIndif", all_orders_and_cat, min_num_indif),
    Property("largestIndif", all_orders_and_cat, largest_indif),
    Property("smallestIndif", all_orders_and_cat, smallest_indif),
    Property("hasCondorcet", all_orders, has_condorcet),
    Property("isSP", ("soc_aaaa", "toc_aaaa"), {
        "soc": lambda x: is_single_peaked(x)[0],
        "toc": lambda x: is_single_peaked_ILP(x)[0]}),
    Property("isSC", ("soc_aaaa",), is_single_crossing),
]
HEADERS = [m.name for m in ALL_PROPERTIES]

DATASET_FOLDER = os.path.join("..", "..", "datasets")

if __name__ == '__main__':
    datasets = [os.path.join(DATASET_FOLDER, ds_dir) for ds_dir in os.listdir(DATASET_FOLDER)]

    all_meta = read_all_metadata_files(DATASET_FOLDER)
    # print(all_meta)
    add_property_value(all_meta, DATASET_FOLDER, ALL_PROPERTIES[0])
    write_all_metadata_files(all_meta, DATASET_FOLDER)

    # for ds in datasets:
    #     compute_dataset_metadata(ds)

    # pool = Pool()
    # for _ in pool.imap_unordered(compute_dataset_metadata, datasets):
    #     pass

