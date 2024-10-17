import zipfile
import os


IN_DIR = os.path.join("..", "datasets")
OUT_DIR = os.path.join("..", "zip")
os.makedirs(OUT_DIR, exist_ok=True)
OUT_DIR_DATASET = os.path.join(OUT_DIR, "dataset")
os.makedirs(OUT_DIR_DATASET, exist_ok=True)
OUT_DIR_TYPE = os.path.join(OUT_DIR, "type")
os.makedirs(OUT_DIR_TYPE, exist_ok=True)

to_zip = ['00062 - orderaltexpe']

try:
    os.makedirs(OUT_DIR)
except FileExistsError as e:
    pass

for ds_dir in os.listdir(IN_DIR):
    if os.path.isdir(os.path.join(IN_DIR, ds_dir)):
        if ds_dir in to_zip:
            print("Zipping... {}".format(ds_dir))
            ds_abb = os.path.basename(os.path.normpath(ds_dir))

            with zipfile.ZipFile(os.path.join(OUT_DIR_DATASET, ds_abb + ".zip"), "w", zipfile.ZIP_DEFLATED) as zip_file:
                for file in os.listdir(os.path.join(IN_DIR, ds_dir)):
                    zip_file.write(os.path.join(IN_DIR, ds_dir, file), file)
    else:
        print("Skipped... {}".format(ds_dir))
