from preflibtools.instances.preflibinstance import OrdinalInstance, CategoricalInstance, MatchingInstance
import preflibtools.instances.sanity as sanity

import os

IN_DIR = "../datasets/"
LOG_DIR = "../log/"

os.makedirs(LOG_DIR, exist_ok=True)

with open(os.path.join(LOG_DIR, "log.html"), "w") as log_file:
    for ds_dir in os.listdir(IN_DIR):
        print("Checking {}".format(ds_dir))
        h1_written = False
        for file in os.listdir(os.path.join(IN_DIR, ds_dir)):
            print("\tChecking {} - {}".format(ds_dir, file))
            extention = os.path.splitext(file)[1][1:]
            if extention in ["soc", "toc", "soi", "toi"]:
                file_path = os.path.join(IN_DIR, ds_dir, file)
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
            elif extention == "cat":
                file_path = os.path.join(IN_DIR, ds_dir, file)
                instance = CategoricalInstance(file_path)

                error_list_metadata = sanity.metadata(instance)
                error_list_categories = sanity.categories(instance)
                if error_list_metadata or error_list_categories:
                    if not h1_written:
                        log_file.write("\n<h1>Dataset " + ds_dir + "</h1>\n")
                        h1_written = True
                    log_file.write("\n<h2>" + instance.file_name + " --- " + ds_dir + "</h2>\n")
                    if error_list_metadata:
                        log_file.write("<h3>Metadata Check</h3>\n")
                        for error in error_list_metadata:
                            log_file.write("<p>" + str(error) + "</p>\n")
                    if error_list_categories:
                        log_file.write("<h3>Preferences Check</h3>\n")
                        for error in error_list_categories:
                            log_file.write("<p>" + str(error) + "</p>\n")
            elif extention == "wmd":
                break
                file_path = os.path.join(IN_DIR, ds_dir, file)
                instance = MatchingInstance(file_path)

                error_list_metadata = sanity.metadata(instance)
                error_list_matching = sanity.matching(instance)
                if error_list_metadata or error_list_matching:
                    if not h1_written:
                        log_file.write("\n<h1>Dataset " + ds_dir + "</h1>\n")
                        h1_written = True
                    log_file.write("\n<h2>" + instance.file_name + " --- " + ds_dir + "</h2>\n")
                    if error_list_metadata:
                        log_file.write("<h3>Metadata Check</h3>\n")
                        for error in error_list_metadata:
                            log_file.write("<p>" + str(error) + "</p>\n")
                    if error_list_matching:
                        log_file.write("<h3>Matching Check</h3>\n")
                        for error in error_list_matching:
                            log_file.write("<p>" + str(error) + "</p>\n")
