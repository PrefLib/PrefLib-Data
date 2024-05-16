import os
import pathlib
from collections.abc import Iterable
from datetime import datetime
from multiprocessing import Pool

import dateutil.parser
import pandas as pd

from preflibtools.instances import get_parsed_instance
from preflibtools.instances.dataset import read_info_file
from preflibtools.properties import num_alternatives, num_voters, num_different_preferences, \
    is_strict, is_complete, is_approval, is_single_peaked, is_single_crossing, largest_ballot, \
    smallest_ballot, max_num_indif, min_num_indif, largest_indif, smallest_indif, has_condorcet, \
    is_single_peaked_ILP


class Property:
    def __init__(self, name, applies_to, func, is_file_property):
        self.name = name
        self.applies_to = applies_to
        self.func = func
        self.is_file_property = is_file_property

    def compute(self, arg, data_type):
        if isinstance(self.func, dict):
            return self.func[data_type](arg)
        else:
            return self.func(arg)

    def applies_to_instance(self, instance):
        return self.applies_to is None or instance.data_type in self.applies_to

    def compute_instance(self, instance):
        if self.applies_to_instance(instance):
            return self.compute(instance, instance.data_type)

    def applies_to_file(self, file):
        return self.applies_to is None or os.path.splitext(file)[1][1:] in self.applies_to

    def compute_file(self, file_path):
        if self.applies_to_file(file_path):
            if self.is_file_property:
                return self.compute(file_path, os.path.splitext(file_path)[1][1:])
            instance = get_parsed_instance(file_path)
            return self.compute(instance, instance.data_type)


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


def write_all_metadata_ds(ds_metadata, root_dir_path, ds_dir):
    column_to_order = []
    if 'file_number' in ds_metadata.columns:
        column_to_order.append('file_number')
    if 'modification_type' in ds_metadata.columns:
        column_to_order.append('modification_type')
    if 'file' in ds_metadata.columns:
        column_to_order.append('file')
    ds_metadata = ds_metadata.sort_values(by=column_to_order)
    if len(ds_metadata) > 0:
        ds_metadata = ds_metadata[HEADERS]
    ds_metadata.to_csv(
        os.path.join(root_dir_path, ds_dir, "metadata.csv"),
        sep=";",
        na_rep="N/A",
        index=False,
        encoding="utf-8",
    )
    print(f"Wrote the metadata file for {ds_dir}.")


def write_all_metadata_files(all_metadata, root_dir_path):
    for ds_dir, metadata in all_metadata.items():
        write_all_metadata_ds(metadata, root_dir_path, ds_dir)


def add_property_value_pool_func(pool_args):
    prop, root_dir_path, directory, metadata_df, force_recompute = pool_args

    def add_property_value_apply_func(df_row):
        file = df_row["file"]
        file_path = os.path.join(root_dir_path, directory, file)
        modif_timestamp = dateutil.parser.parse(df_row["last_modif"])
        current_modif_timestamp = datetime.fromtimestamp(pathlib.Path(file_path).stat().st_mtime)
        if prop.name not in df_row or force_recompute or current_modif_timestamp != modif_timestamp:
            print(f"\t\t{file} - Computing {prop.name}")
            return prop.compute_file(os.path.join(root_dir_path, directory, df_row["file"]))
        print(
            f"\t\t{file} - Skipped ({prop.name in df_row} or {not force_recompute} or {current_modif_timestamp == modif_timestamp})")
        return df_row[prop.name]

    if len(metadata_df) > 0:
        metadata_df[prop.name] = metadata_df.apply(add_property_value_apply_func, axis=1)
    print(f"\t{directory} with {len(metadata_df)} files")
    return directory, metadata_df


def add_property_value(all_metadata, root_dir_path, prop, write=False, force_recompute=False, num_workers=1):
    print(f"Computing {prop.name} for datasets:")

    pool = Pool(processes=num_workers)
    pool_args = [(prop, root_dir_path, ds_dir, meta_df, force_recompute) for ds_dir, meta_df in all_metadata.items()]
    for dir_metadata in pool.imap_unordered(add_property_value_pool_func, pool_args):
        d, m = dir_metadata
        all_metadata[d] = m
        if write:
            write_all_metadata_ds(m, root_dir_path, d)


def update_properties_pool_func(pool_args):
    all_properties, root_dir_path, directory, metadata_df, force_recompute = pool_args

    def update_properties_apply_func(df_row):
        file = df_row["file"]
        file_path = os.path.join(root_dir_path, directory, file)
        modif_timestamp = dateutil.parser.parse(df_row["last_modif"])
        current_modif_timestamp = datetime.fromtimestamp(pathlib.Path(file_path).stat().st_mtime)
        force_compute_all = False
        force_to_compute = []
        if isinstance(force_recompute, Iterable):
            if isinstance(force_recompute, str):
                force_to_compute = [force_recompute]
            else:
                force_to_compute = force_recompute
        elif isinstance(force_recompute, bool) and force_recompute:
            force_compute_all = True
        if force_compute_all or len(force_to_compute) > 0 or current_modif_timestamp != modif_timestamp:
            if force_recompute:
                print(f"\t\tUpdating {file} (force_recompute = True)")
            else:
                print(f"\t\tUpdating {file} (time stamp is {current_modif_timestamp} vs "
                      f"{modif_timestamp})")
            for prop in all_properties:
                if len(force_to_compute) > 0:
                    if prop.name in force_to_compute:
                        df_row[prop.name] = prop.compute_file(file_path)
                else:
                    df_row[prop.name] = prop.compute_file(file_path)
        return df_row

    print(f"\t{directory} with {len(metadata_df)} files")
    metadata_df.apply(update_properties_apply_func, axis=1)
    return directory, metadata_df


def update_properties(all_metadata, root_dir_path, all_properties, force_recompute=False, num_workers=1):
    print(f"Updating properties for datasets:")
    pool = Pool(processes=num_workers)
    pool_args = [(all_properties, root_dir_path, ds_dir, meta_df, force_recompute) for ds_dir, meta_df in all_metadata.items()]
    for ds_dir, metadata in pool.imap_unordered(update_properties_pool_func, pool_args):
        write_all_metadata_ds(metadata, root_dir_path, ds_dir)
        all_metadata[ds_dir] = metadata


def get_file_name(file_path):
    return os.path.basename(file_path)


def get_file_number(file_path):
    return int(os.path.basename(file_path).split(".")[0].split("-")[1])


def get_last_modif_time(file_path):
    return datetime.fromtimestamp(pathlib.Path(file_path).stat().st_mtime)


def get_modification_type(file_path):
    ds_dir = os.path.abspath(os.path.join(file_path, os.pardir))
    info = read_info_file(os.path.join(ds_dir, "info.txt"))
    return info['files'][os.path.basename(file_path)]['modification_type']


def is_single_peaked_soc(instance):
    return is_single_peaked(instance)[0]


def is_single_peaked_toc(instance):
    return is_single_peaked_ILP(instance)[0]


ALL_ORDERS_FORMATS = ("soc", "soi", "toc", "toi")
ALL_ORDINAL_FORMATS = ("soc", "soi", "toc", "toi", "cat")
ALL_PREFERENCES_FORMATS = ("soc", "soi", "toc", "toi", "cat", "wmd")
ALL_PROPERTIES_LIST = [
    Property("file", None, get_file_name, True),
    Property("file_number", None, get_file_number, True),
    Property("last_modif", None, get_last_modif_time, True),
    Property("modification_type", None, get_modification_type, True),
    Property("numAlt", ALL_PREFERENCES_FORMATS, num_alternatives, False),
    Property("numVot", ALL_PREFERENCES_FORMATS, num_voters, False),
    Property("numUniq", ALL_ORDINAL_FORMATS, num_different_preferences, False),
    Property("isStrict", ALL_ORDERS_FORMATS, is_strict, False),
    Property("isComplete", ALL_ORDINAL_FORMATS, is_complete, False),
    Property("isApproval", ALL_ORDINAL_FORMATS, is_approval, False),
    Property("largestBallot", ALL_ORDINAL_FORMATS, largest_ballot, False),
    Property("smallestBallot", ALL_ORDINAL_FORMATS, smallest_ballot, False),
    Property("maxNumIndif", ALL_ORDINAL_FORMATS, max_num_indif, False),
    Property("minNumIndif", ALL_ORDINAL_FORMATS, min_num_indif, False),
    Property("largestIndif", ALL_ORDINAL_FORMATS, largest_indif, False),
    Property("smallestIndif", ALL_ORDINAL_FORMATS, smallest_indif, False),
    Property("hasCondorcet", ALL_ORDERS_FORMATS, has_condorcet, False),
    Property("isSP", ("soc", "toc"), {
        "soc": is_single_peaked_soc,
        "toc": is_single_peaked_toc}, False),
    Property("isSC", ("soc",), is_single_crossing, False),
]
ALL_PROPERTIES = {p.name: p for p in ALL_PROPERTIES_LIST}
HEADERS = list(ALL_PROPERTIES)

DATASET_FOLDER = os.path.join("..", "..", "datasets")


def main():
    all_meta = read_all_metadata_files(DATASET_FOLDER)
    update_properties(all_meta, DATASET_FOLDER, ALL_PROPERTIES_LIST, force_recompute=["numAlt", "numVot"], num_workers=10)
    # add_property_value(all_meta, DATASET_FOLDER, ALL_PROPERTIES["modification_type"], write=True, force_recompute=True, num_workers=6)
    # write_all_metadata_files(all_meta, DATASET_FOLDER)


if __name__ == '__main__':
    main()
