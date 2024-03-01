import os

from preflibtools.instances.preflibinstance import OrdinalInstance


IN_DIR = "../datasets/"

for ds_dir in os.listdir(IN_DIR):
    if os.path.isdir(os.path.join(IN_DIR, ds_dir)):
        if ds_dir == "web":
            for file in os.listdir(os.path.join(IN_DIR, ds_dir)):
                if os.path.splitext(file)[1][1:] in ["soc", "toc", "soi", "toi"]:
                    file_path = os.path.join(IN_DIR, ds_dir, file)
                    instance = OrdinalInstance(file_path)
                    if len(set(instance.alternatives_name.values())) < instance.num_alternatives:
                        inst = OrdinalInstance()
                        inst.parse_file(file_path, autocorrect=True)
                        inst.write(file_path)
