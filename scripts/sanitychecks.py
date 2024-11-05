import warnings

from preflibtools.instances.preflibinstance import get_parsed_instance
from preflibtools.instances.dataset import read_info_file
import preflibtools.instances.sanity as sanity

import os

IN_DIR = "../datasets/"

for ds_dir in sorted(os.listdir(IN_DIR), reverse=True):
    print("Checking {}".format(ds_dir))
    h1_written = False
    for file in os.listdir(os.path.join(IN_DIR, ds_dir)):
        print(f"\t{file}")
        file_path = os.path.join(IN_DIR, ds_dir, file)
        if file == "info.txt":
            infos = read_info_file(file_path)
            info_error_list = []
            number_files = len([f for f in os.listdir(os.path.join(IN_DIR, ds_dir)) if os.path.isfile(os.path.join(IN_DIR, ds_dir, f)) and f not in ["info.txt", "metadata.csv"]])
            if not len(infos["files"]) == number_files:
                info_error_list.append(f"{ds_dir} - Info says {len(infos['files'])} but there are {number_files} files")
            if not set(infos["files"]) == set(f for f in os.listdir(os.path.join(IN_DIR, ds_dir)) if f not in ["info.txt", "metadata.csv"]):
                info_error_list.append(f"{ds_dir} - Not all files in infos or some non-existing files in info")
            for error in info_error_list:
                warnings.warn(f"{ds_dir} - Info: {error}")
        else:
            extention = os.path.splitext(file)[1][1:]
            if extention in ["soc", "toc", "soi", "toi", "cat"]:
                instance = get_parsed_instance(file_path)

                metadata_error_list = sanity.metadata(instance)
                if metadata_error_list:
                    for error in metadata_error_list:
                        warnings.warn(f"{ds_dir} - {instance.file_name}: {error}")
                if extention in ["soc", "toc", "soi", "toi"]:
                    order_error_list = sanity.orders(instance)
                    if order_error_list:
                        for error in order_error_list:
                            warnings.warn(f"{ds_dir} - {instance.file_name}: {error}")

