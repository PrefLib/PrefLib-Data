import shutil
import sys
import os
import traceback

from preflibtools.instances import OrdinalInstance
import preflibtools.instances.sanity as sanity

abb_dict = {
    "boardgames": "Boardgames Geek Ranking",
    "boxing": "Boxing",
    "weeksport": "Weeks Power Ranking",
    "combinedsport": "Combined Power Ranking",
    "countries": "Countries Ranking",
    "f1races": "Formula 1 Races",
    "f1seasons": "Formula 1 Seasons",
    "movehub": "Movehub City Ranking",
    "mylaps": "Multilaps Competitions",
    "cycling": "Cycling Races",
    "seasonsport": "Seasons Power Ranking",
    "spotifyday": "Spotify Daily Chart",
    "spotifycountry": "Spotify Countries Chart",
    "tabletennis": "Table Tennis Ranking",
    "tennis": "Tennis Ranking",
    "university": "Global University Ranking",
}

num_dict = {
    "boardgames": 41,
    "boxing": 42,
    "weeksport": 54,
    "combinedsport": 55,
    "countries": 51,
    "f1races": 53,
    "f1seasons": 52,
    "movehub": 50,
    "mylaps": 49,
    "cycling": 43,
    "seasonsport": 56,
    "spotifyday": 47,
    "spotifycountry": 48,
    "tabletennis": 44,
    "tennis": 45,
    "university": 46,
}


def count_duplicates(in_folder):
    num_duplicates_files = 0
    for ds_folder in os.listdir(in_folder):
        print(ds_folder)
        for data_file in os.listdir(os.path.join(in_folder, ds_folder)):
            if data_file.endswith("_raw.soc"):
                root_name = data_file[:-8]
                if os.path.exists(os.path.join(in_folder, ds_folder, root_name + "_complete.soc")):
                    num_duplicates_files += 1
    print("I found {} duplicates.".format(num_duplicates_files))
    return num_duplicates_files


def remove_duplicated_files(old_main_folder_path, new_main_folder_name):
    new_main_folder_path = os.path.join("..", "..", "Niclas", new_main_folder_name)
    os.makedirs(new_main_folder_path, exist_ok=True)
    for ds_folder in os.listdir(old_main_folder_path):
        new_ds_folder = os.path.join("..", "..", "Niclas", new_main_folder_name, ds_folder)
        os.makedirs(new_ds_folder, exist_ok=True)
        print(ds_folder)
        for data_file in os.listdir(os.path.join(old_main_folder_path, ds_folder)):
            # If the raw is an soi, we copy it and check for a potential _complete.soc to copy as well
            if data_file.endswith("_raw.soi"):
                root_name = data_file[:-8]
                shutil.copy(os.path.join(old_main_folder_path, ds_folder, data_file),
                            os.path.join("..", "..", "Niclas", new_main_folder_name, ds_folder, data_file))
                if os.path.exists(os.path.join(old_main_folder_path, ds_folder, root_name + "_complete.soc")):
                    shutil.copy(os.path.join(old_main_folder_path, ds_folder, root_name + "_complete.soc"),
                                os.path.join("..", "..", "Niclas", new_main_folder_name, ds_folder,
                                             root_name + "_complete.soc"))
            # If the raw is an soc, we copy it and ignore a potential _complete.soc
            if data_file.endswith("_raw.soc") or data_file == "description":
                shutil.copy(os.path.join(old_main_folder_path, ds_folder, data_file),
                            os.path.join("..", "..", "Niclas", new_main_folder_name, ds_folder, data_file))


def convert_new_format(in_folder, out_folder):
    for ds_folder in os.listdir(in_folder):
        print(ds_folder)
        new_ds_folder = os.path.join(out_folder, "000{} - {}".format(num_dict[ds_folder], ds_folder))
        os.makedirs(new_ds_folder, exist_ok=True)

        # We parse and re-write the data files
        files = [file for file in os.listdir(os.path.join(in_folder, ds_folder)) if
                 file.endswith("_raw.soi") or file.endswith("_raw.soc")]
        files.sort()
        file_index = 1
        instances = []
        for data_file in files:
            print("\t{} - {}".format(ds_folder, data_file))
            instance = OrdinalInstance()
            with open(os.path.join(in_folder, ds_folder, data_file), encoding="utf-8") as file:
                lines = file.readlines()
            instance.parse_old(lines)
            instance.recompute_cardinality_param()
            instance.title = os.path.splitext(data_file)[0][:-4].replace("_", " ").title()
            instance.description = ""
            instance.data_type = os.path.splitext(data_file)[1][1:]
            instance.modification_type = "original"
            instance.publication_date = "2022-09-25"
            instance.modification_date = "2022-09-25"
            new_file_name = "000{}-0000{}{}{}{}.{}".format(num_dict[ds_folder],
                                                           "0" if file_index <= 999 else "",
                                                           "0" if file_index <= 99 else "",
                                                           "0" if file_index <= 9 else "",
                                                           file_index,
                                                           instance.data_type)
            instance.file_name = new_file_name
            instances.append(instance)
            # If it's a _raw.soi, there could also be a _complete.soc
            if data_file.endswith("_raw.soi"):
                soc_file_name = os.path.splitext(data_file)[0][:-4] + "_complete.soc"
                if os.path.exists(os.path.join(in_folder, ds_folder, soc_file_name)):
                    instance.related_files = os.path.splitext(new_file_name)[0] + ".soc"
                    soc_instance = OrdinalInstance()
                    with open(os.path.join(in_folder, ds_folder, soc_file_name), encoding="utf-8") as file:
                        lines = file.readlines()
                    soc_instance.parse_old(lines)
                    soc_instance.recompute_cardinality_param()
                    soc_instance.title = os.path.splitext(data_file)[0][:-4].replace("_", " ").title()
                    soc_instance.description = "Complete preferences extracted from the soi file"
                    soc_instance.data_type = "soc"
                    soc_instance.modification_type = "induced"
                    soc_instance.publication_date = "2022-09-25"
                    soc_instance.modification_date = "2022-09-25"
                    soc_instance.relates_to = new_file_name
                    soc_instance.file_name = os.path.splitext(new_file_name)[0] + ".soc"
                    soc_instance.write(os.path.join(new_ds_folder, os.path.splitext(new_file_name)[0] + ".soc"))
                    instances.append(soc_instance)

            instance.write(os.path.join(new_ds_folder, new_file_name))
            file_index += 1

        # Writing the info file, the file section is purposefully omitted.
        with open(os.path.join(new_ds_folder, "info.txt"), "w", encoding="utf-8") as info_file:
            with open(os.path.join(in_folder, ds_folder, "description"), encoding="utf-8") as descr_file:
                descr_lines = descr_file.readlines()
                descr = descr_lines[1:-2]
                descr = ' '.join(["<p>" + line.strip() + "</p>" for line in descr if len(line) > 3])
                descr = "<p>" + descr[16:]
                info_file.write("Name: {}\n\n".format(abb_dict[ds_folder]))
                info_file.write("Abbreviation: {}\n\n".format(ds_folder))
                info_file.write("Tags: Election\n\n")
                info_file.write("Series Number: 000{}\n\n".format(num_dict[ds_folder]))
                info_file.write("Publication Date: 2022-09-25\n\n")
                info_file.write("Description: {}\n\n".format(descr))
                info_file.write("Required Citations: Niclas Boehmer and Nathan Schaar. <em>Collecting, Classifying, "
                                "Analyzing, and Using Real-World Elections</em>. Arxiv.org/abs/2204.03589, 2022 "
                                "(<a href=\"/static/bib/BoSc22.bib\">Bibtex</a>).\n\n")
                info_file.write("Selected Studies:\n\n")
                info_file.write("file_name, modification_type, relates_to, title, description, publication_date\n")
                for instance in instances:
                    info_file.write("{}, {}, {}, {}, {}, {}\n".format(instance.file_name, instance.modification_type,
                                                                      instance.relates_to, instance.title,
                                                                      instance.description, instance.publication_date))


def sanity_checks(in_folder, log_dir):
    with open(os.path.join(log_dir, "log.html"), "w") as log_file:
        for ds_dir in os.listdir(in_folder):
            print("Checking {}".format(ds_dir))
            h1_written = False
            for file in os.listdir(os.path.join(in_folder, ds_dir)):
                print("\tChecking {} - {}".format(ds_dir, file))
                extention = os.path.splitext(file)[1][1:]
                if extention in ["soc", "soi"]:
                    file_path = os.path.join(in_folder, ds_dir, file)
                    instance = OrdinalInstance(file_path)

                    error_list_metadata = sanity.metadata(instance)
                    error_list_orders = sanity.orders(instance)
                    if error_list_metadata or error_list_orders:
                        if not h1_written:
                            log_file.write("\n<h1>Dataset " + ds_dir + "</h1>\n")
                            h1_written = True
                        log_file.write("\n<h2>" + instance.file_name + " --- " + ds_dir + "</h2>\n")
                        if error_list_metadata:
                            log_file.write("<h3>Metadata Check</h3>\n")
                            for error in error_list_metadata:
                                log_file.write("<p>" + str(error) + "</p>\n")
                        if error_list_orders:
                            log_file.write("<h3>Orders Check</h3>\n")
                            for error in error_list_orders:
                                log_file.write("<p>" + str(error) + "</p>\n")


niclas_in = os.path.join("..", "..", "Niclas", "In")

new_in_folder_name = "In_No_Duplicates"
# remove_duplicated_files(niclas_in, new_in_folder_name)
# count_duplicates(niclas_in)
new_in_folder = os.path.join(os.path.dirname(niclas_in), new_in_folder_name)


niclas_out = os.path.join("..", "..", "Niclas", "Out")
convert_new_format(new_in_folder, niclas_out)


# sanity_checks(niclas_out, os.path.join("..", "..", "log"))
