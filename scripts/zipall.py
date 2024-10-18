import zipfile
import os

IN_DIR = os.path.join("..", "datasets")
OUT_DIR = os.path.join("..", "zip")
os.makedirs(OUT_DIR, exist_ok=True)


def zip_types():
    for data_type in ("toc", "toi", "soc", "soi", "cat", "wmd"):
        print("Zipping... {}".format(data_type))
        all_files = []
        for dataset_dir in sorted(os.listdir(IN_DIR)):
            for datafile_name in os.listdir(os.path.join(IN_DIR, dataset_dir)):
                if datafile_name.endswith(data_type):
                    all_files.append((os.path.join(IN_DIR, dataset_dir, datafile_name), datafile_name))

        with zipfile.ZipFile(os.path.join(OUT_DIR, data_type + ".zip"), "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_path, file_name in all_files:
                zip_file.write(file_path, file_name)


def zip_datasets():
    for ds_dir in sorted(os.listdir(IN_DIR)):
        if os.path.isdir(os.path.join(IN_DIR, ds_dir)):
            print("Zipping... {}".format(ds_dir))
            ds_abb = os.path.basename(os.path.normpath(ds_dir))

            with zipfile.ZipFile(os.path.join(OUT_DIR, ds_abb + ".zip"), "w", zipfile.ZIP_DEFLATED) as zip_file:
                for file in os.listdir(os.path.join(IN_DIR, ds_dir)):
                    zip_file.write(os.path.join(IN_DIR, ds_dir, file), file)
        else:
            print("Skipped... {}".format(ds_dir))


if __name__ == "__main__":
    zip_datasets()
    zip_types()
