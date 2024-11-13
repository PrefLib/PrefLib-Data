import argparse
import warnings

from preflibtools.instances.preflibinstance import get_parsed_instance
from preflibtools.instances.dataset import read_info_file
import preflibtools.instances.sanity as sanity

import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IN_DIR = os.path.join(SCRIPT_DIR, "../datasets")


def check_dataset(ds_dir, escalate_warnings):
    """Run sanity checks on a dataset directory and escalate warnings if specified."""
    print(f"Checking {ds_dir}")
    info_file_path = os.path.join(IN_DIR, ds_dir, "info.txt")
    dataset_files = sorted(os.listdir(os.path.join(IN_DIR, ds_dir)))

    # Check info.txt file if it exists
    if "info.txt" in dataset_files:
        print(f"\tinfo.txt")
        check_info_file(info_file_path, ds_dir, dataset_files, escalate_warnings)

    # Check other files in the dataset
    for file in dataset_files:
        print(f"\t{file}")
        if file != "info.txt":
            check_file(ds_dir, file, escalate_warnings)


def check_info_file(info_file_path, ds_dir, dataset_files, escalate_warnings):
    """Checks the contents of info.txt for consistency with the actual files in the directory."""
    infos = read_info_file(info_file_path)
    info_error_list = []
    # Files to be checked in directory
    actual_files = [f for f in dataset_files if f not in ["info.txt", "metadata.csv"]]

    # Validate file counts
    if len(infos["files"]) != len(actual_files):
        info_error_list.append(
            f"Info says {len(infos['files'])} files but found {len(actual_files)} files")

    # Validate file names
    if set(infos["files"]) != set(actual_files):
        info_error_list.append("Mismatch between files listed in info and files in directory")

    # Report or escalate any errors found
    handle_errors(info_error_list, ds_dir, escalate_warnings)


def check_file(ds_dir, file, escalate_warnings):
    """Run sanity checks on individual files in a dataset directory."""
    file_path = os.path.join(IN_DIR, ds_dir, file)
    extension = os.path.splitext(file)[1][1:]

    if extension in ["soc", "toc", "soi", "toi", "cat"]:
        instance = get_parsed_instance(file_path)

        # Metadata check
        metadata_errors = sanity.metadata(instance)
        handle_errors(metadata_errors, f"{ds_dir} - {instance.file_name}", escalate_warnings)

        # Order check for specific file types
        if extension in ["soc", "toc", "soi", "toi"]:
            order_errors = sanity.orders(instance)
            handle_errors(order_errors, f"{ds_dir} - {instance.file_name}", escalate_warnings)


def handle_errors(error_list, context, escalate_warnings):
    """Handle errors by warning or escalating them based on the flag."""
    for error in error_list:
        message = f"{context}: {error}"
        if escalate_warnings:
            raise ValueError(message)
        else:
            warnings.warn(message)


def main():
    parser = argparse.ArgumentParser(description="Run sanity checks on PrefLib datasets.")
    parser.add_argument(
        "--escalate-warnings",
        action="store_true",
        help="Escalate warnings to errors"
    )
    args = parser.parse_args()

    # Run checks on each dataset directory
    for ds_dir in sorted(os.listdir(IN_DIR), reverse=True):
        check_dataset(ds_dir, args.escalate_warnings)


if __name__ == "__main__":
    main()
