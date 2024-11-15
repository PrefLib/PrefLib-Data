from __future__ import annotations

import argparse
import csv
import os
import pathlib
from collections.abc import Iterable, Callable, Collection
from datetime import datetime
from enum import IntEnum
from functools import partial
from multiprocessing import Pool

import dateutil.parser
import pandas as pd

from preflibtools.instances import get_parsed_instance, PrefLibInstance
from preflibtools.instances.dataset import read_info_file
from preflibtools.properties import num_alternatives, num_voters, num_different_preferences, \
    is_approval, has_condorcet, is_strict, is_complete
from preflibtools.properties.subdomains.ordinal import is_single_peaked, is_single_peaked_pq_tree, \
    is_single_crossing
from preflibtools.properties.subdomains.ordinal.singlepeaked import is_single_peaked_on_tree


class SPEED(IntEnum):
    SLOW = 1
    MEDIUM = 2
    FAST = 3


SPEED_MAPPING = {
    "slow": SPEED.SLOW,
    "medium": SPEED.MEDIUM,
    "fast": SPEED.FAST,
}


class Property:
    """Class representing a property to compute. Each property is a cell in the metadata CSV
    file."""

    def __init__(
            self,
            name: str,
            applies_to: Collection[str] | None,
            func: Callable | dict[str, Callable],
            is_file_property: bool,
            speed: SPEED | None = None,
            max_num_voters: dict[SPEED, int] = None,
            max_num_alternatives: dict[SPEED, int] = None
    ):
        self.name = name
        self.applies_to = applies_to
        self.func = func
        self.is_file_property = is_file_property
        self.speed = speed
        if max_num_voters is None:
            max_num_voters = dict()
        self.max_num_voters = max_num_voters
        if max_num_alternatives is None:
            max_num_alternatives = dict()
        self.max_num_alternatives = max_num_alternatives

    def compute(self, arg, data_type: str):
        """Compute the property by applying the function. If self.func is a dict, then it indicates
        different functions for different data types, we select the correct one."""
        if isinstance(self.func, dict):
            return self.func[data_type](arg)
        else:
            return self.func(arg)

    def is_fast_enough(self, speed: SPEED):
        """Checks if the speed is fast enough for the property."""
        return self.speed is None or self.speed >= speed

    def applies_to_instance(self, instance: PrefLibInstance, speed: SPEED):
        """Checks whether the property can be computed for the instance."""
        # If it is a slower property than required then no
        if not self.is_fast_enough(speed):
            return False
        # If it does not apply to the data type then no
        if self.applies_to is None or instance.data_type not in self.applies_to:
            return False
        # Check for bounds
        num_alts = num_alternatives(instance)
        num_vots = num_voters(instance)
        alt_bound = self.max_num_alternatives.get(speed, float("inf"))
        vot_bound = self.max_num_voters.get(speed, float("inf"))
        return num_alts <= alt_bound and num_vots <= vot_bound

    def compute_instance(self, instance: PrefLibInstance, speed: SPEED):
        """Compute the property on the instance passed as argument."""
        if self.applies_to_instance(instance, speed):
            return self.compute(instance, instance.data_type)

    def applies_to_file(self, file_path: str):
        """Checks whether the property can be computed for the given file. Performs fewer checks
        than applies_to_instance."""
        return self.applies_to is None or os.path.splitext(file_path)[1][1:] in self.applies_to

    def compute_file(self, file_path: str, speed: SPEED, pre_parsed_instance: PrefLibInstance = None):
        """Compute the property on the file passed as argument."""
        if self.applies_to_file(file_path):
            if self.is_file_property:
                return self.compute(file_path, os.path.splitext(file_path)[1][1:])
            if pre_parsed_instance is None:
                pre_parsed_instance = get_parsed_instance(file_path)
            return self.compute_instance(pre_parsed_instance, speed)

    def __str__(self):
        return f"Prop[{self.name}]"

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name.__eq__(other)

    def __le__(self, other):
        return self.name.__le__(other)

    def __lt__(self, other):
        return self.name.__lt__(other)

    def __ge__(self, other):
        return self.name.__ge__(other)

    def __gt__(self, other):
        return self.name.__gt__(other)


def compute_file_properties(file_path_and_property_list: Collection[str, Iterable[Property]], speed: SPEED):
    """Computes the properties for a given file."""
    file_path, property_list = file_path_and_property_list
    if file_path[-3:] not in ("soc", "soi", "toc", "toi", "cat", "wmd"):
        return None, None
    if len(property_list) == 0:
        return None, None
    file_name = os.path.basename(file_path)
    print(f"\t{file_name} - {tuple(p.name for p in property_list)}")
    results = {}
    instance = get_parsed_instance(file_path)
    for prop in property_list:
        res = prop.compute_file(file_path, speed, pre_parsed_instance=instance)
        if res is not None:
            results[prop.name] = res
    return file_name, results


def compute_dataset_metadata(
        root_dir_path: str,
        all_considered_properties: Iterable[Property],
        speed: SPEED,
        max_num_processes: int = 4,
        properties_to_always_compute: Iterable[Property] = None,
        force_recompute: bool = False
):
    """Computes the metadata for a dataset spanning multiple processes. Skips files that have not
    been modified since last computation.

    If force_recompute = True, properties are compute for all files and not just the ones that have been modified since
    last computation.

    The properties in properties_to_always_compute are always recomputed.
    """
    if properties_to_always_compute is None:
        properties_to_always_compute = []
    print(f"Computing for {root_dir_path}")
    info = read_info_file(os.path.join(root_dir_path, "info.txt"))

    # Retrieve the current metadata info if existing
    metadata_file_path = os.path.join(root_dir_path, "metadata.csv")
    old_headers = set()
    old_metadata = dict()
    if os.path.exists(metadata_file_path):
        with open(metadata_file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            old_metadata = {r["file"]: r for r in reader}
            for meta_dict in old_metadata.values():
                old_headers = set(meta_dict)
                break

    # Discard the content of the metadata file and write the header
    headers = [p.name for p in all_considered_properties]
    with open(metadata_file_path, "w", encoding="utf-8") as out_file:
        out_file.write(";".join(headers) + "\n")
    if set(headers) != old_headers:
        force_recompute = True

    # Collect all files that are to be updated: those that have been modified since last time
    file_paths_to_compute_properties = dict()
    all_metadata_rows = dict()
    for file in info["files"]:
        file_path = os.path.join(root_dir_path, file)
        if force_recompute:
            file_paths_to_compute_properties[file_path] = all_considered_properties
        else:
            last_modif = old_metadata.get(file, dict()).get("last_modif")
            if last_modif is not None:
                last_modif = dateutil.parser.parse(last_modif)
            current_modif_time = get_last_modif_time(file_path)
            if last_modif is None or current_modif_time > last_modif:
                file_paths_to_compute_properties[file_path] = all_considered_properties
            else:
                old_meta = old_metadata[file]
                properties_to_compute = list(properties_to_always_compute)
                for prop in all_considered_properties:
                    if prop not in properties_to_always_compute and old_meta[prop.name] == "N/A":
                        properties_to_compute.append(prop)
                file_paths_to_compute_properties[file_path] = list(properties_to_always_compute)
                all_metadata_rows[file] = old_metadata[file]

    # Compute the necessary metadata in a pool
    file_pool = Pool(min(max_num_processes, os.cpu_count()))
    compute_with_fixed_params = partial(compute_file_properties, speed=speed)
    for file, metadata in file_pool.imap_unordered(compute_with_fixed_params, file_paths_to_compute_properties.items()):
        if metadata is not None:
            row = all_metadata_rows.get(file)
            # If a row already exists, we update with the new values
            if row:
                for m, v in metadata.items():
                    row[m] = v
            else:
                all_metadata_rows[file] = metadata

    # Include the non-computed ones
    with open(metadata_file_path, "a", encoding="utf-8") as out_file:
        for metadata in sorted(all_metadata_rows.values(), key=metadata_ordering_key):
            meta_write = [str(metadata[h]) if h in metadata else "N/A" for h in headers]
            out_file.write(";".join(meta_write) + "\n")


def metadata_ordering_key(meta_dict):
    """Returns the key used to order metadata"""
    if "file_number" in meta_dict:
        modif_type = meta_dict.get("modification_type")
        if modif_type == "original":
            modif_type_modifier = -0.4
        elif modif_type == "induced":
            modif_type_modifier = -0.3
        elif modif_type == "imbued":
            modif_type_modifier = -0.2
        elif modif_type == "synthetic":
            modif_type_modifier = -0.1
        else:
            modif_type_modifier = 0
        return int(meta_dict["file_number"]) + modif_type_modifier
    return meta_dict["file"]


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


def is_single_crossing_soc(instance):
    return is_single_crossing(instance)[0]


def is_single_peaked_soc(instance):
    return is_single_peaked(instance)[0]


def is_single_peaked_toc(instance):
    if len(instance.alternatives_name) < 15:
        return is_single_peaked_pq_tree(instance)


def is_single_peaked_on_tree_soc(instance):
    return is_single_peaked_on_tree(instance)[0]


def bounded_has_condorcet(instance):
    if len(instance.alternatives_name) < 500:
        return has_condorcet(instance)


def none_func(x):
    return


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
    Property("isApproval", ALL_ORDINAL_FORMATS, is_approval, False),
    Property("isStrict", ALL_ORDERS_FORMATS, is_strict, False),
    Property("isComplete", ALL_ORDINAL_FORMATS, is_complete, False),
    Property("hasCondorcet", ALL_ORDERS_FORMATS, bounded_has_condorcet, False),
    Property("isSP", ("soc", "toc"), {
        "soc": is_single_peaked_soc,
        "toc": is_single_peaked_toc}, False),
    Property("isSC", ("soc",), is_single_crossing_soc, False),
    Property("isSPTree", ("soc",), is_single_peaked_on_tree_soc, False),
]
ALL_PROPERTIES_BY_NAME = {p.name: p for p in ALL_PROPERTIES_LIST}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_FOLDER = os.path.join(SCRIPT_DIR, "..", "datasets")


def main():
    parser = argparse.ArgumentParser(description="Compute dataset properties with specified speed.")
    parser.add_argument(
        "--speed",
        choices=["fast", "medium", "slow"],
        default="fast",  # Set default to "fast" if no speed is provided
        help="Computation speed for properties (default: fast)."
    )
    args = parser.parse_args()

    speed = SPEED_MAPPING[args.speed]
    filtered_properties = [p for p in ALL_PROPERTIES_LIST if p.is_fast_enough(speed)]

    for ds_dir in sorted(os.listdir(DATASET_FOLDER), reverse=True):
        compute_dataset_metadata(
            os.path.join(DATASET_FOLDER, ds_dir),
            ALL_PROPERTIES_LIST,
            speed,
            force_recompute=False,
            properties_to_always_compute=[]
        )


if __name__ == '__main__':
    main()
