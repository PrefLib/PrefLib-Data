import zipfile
import os

IN_DIR = "../datasets/"
OUT_DIR = "../zip/"

try:
    os.makedirs(OUT_DIR)
except FileExistsError as e:
    pass

for ds_dir in os.listdir(IN_DIR):
    if os.path.isdir(os.path.join(IN_DIR, ds_dir)):
        print("Zipping... {}".format(ds_dir))
        ds_abb = os.path.basename(os.path.normpath(ds_dir))

        zip_file = zipfile.ZipFile(os.path.join(OUT_DIR, ds_abb + ".zip"), "w", zipfile.ZIP_DEFLATED)

        for file in os.listdir(os.path.join(IN_DIR, ds_dir)):
            zip_file.write(os.path.join(IN_DIR, ds_dir, file), file)

        zip_file.close()
    else:
        print("Skipped... {}".format(ds_dir))
