# Rename the alternatives of a dataset so that each name is unique.

import os

from preflibtools.instances import get_parsed_instance

IN_DIR = "../../datasets/"

for ds_dir in sorted(os.listdir(IN_DIR)):
    if os.path.isdir(os.path.join(IN_DIR, ds_dir)):
        if ds_dir == "00061 - kusama":
            for file in sorted(os.listdir(os.path.join(IN_DIR, ds_dir))):
                if os.path.splitext(file)[1][1:] in ["soc", "toc", "soi", "toi", "cat"]:
                    file_path = os.path.join(IN_DIR, ds_dir, file)
                    instance = get_parsed_instance(file_path)
                    if len(set(instance.alternatives_name.values())) < instance.num_alternatives:
                        print(f"Renamed alts for: {file}")
                        inst = get_parsed_instance(file_path, autocorrect=True)
                        inst.write(file_path)
