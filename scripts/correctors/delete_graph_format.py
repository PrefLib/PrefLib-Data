import os

IN_DIR = "../../datasets/"
OUT_DIR = "../trash/"

try:
    os.makedirs(OUT_DIR)
except FileExistsError as e:
    pass

for ds_dir in os.listdir(IN_DIR):
    if os.path.isdir(os.path.join(IN_DIR, ds_dir)):
        for file in os.listdir(os.path.join(IN_DIR, ds_dir)):
            if os.path.splitext(file)[1] in [".tog", ".mjg", ".wmg", ".pwg"]:
                try:
                    os.makedirs(os.path.join(OUT_DIR, ds_dir))
                except FileExistsError as e:
                    pass
                os.rename(os.path.join(IN_DIR, ds_dir, file), os.path.join(OUT_DIR, ds_dir, file))
