from preflibtools.instances.preflibinstance import OrdinalInstance, MatchingInstance

import sys, os

DS_DIR = "../../datasets/"
OLD_DS_DIR = "../../datasets_old_format/"

for ds_dir in os.listdir(OLD_DS_DIR):
    print("Checking {}".format(ds_dir))
    h1_written = False
    for file in os.listdir(os.path.join(OLD_DS_DIR, ds_dir)):
        if os.path.exists(os.path.join(DS_DIR, ds_dir, file)):
            print("\tChecking {} - {}".format(ds_dir, file))
            extention = os.path.splitext(file)[1][1:]
            if extention in ["soc", "toc", "soi", "toi"]:
                file_path_old = os.path.join(OLD_DS_DIR, ds_dir, file)
                instance_old = OrdinalInstance()
                with open(file_path_old, 'r') as old_file:
                    instance_old.parse_old(old_file.readlines())

                file_path = os.path.join(DS_DIR, ds_dir, file)
                instance = OrdinalInstance(file_path)

                for order in instance_old.orders:
                    if order not in instance.orders:
                        print("{} not found in the new instance".format(order))
                        sys.exit()
                    if instance_old.multiplicity[order] != instance.multiplicity[order]:
                        print("Multiplicity differs for {} between old {} and new {} instance".format(
                            order, instance_old.multiplicity[order], instance.multiplicity[order]))
                        sys.exit()

                for order in instance.orders:
                    if order not in instance_old.orders:
                        print("{} not found in the old instance".format(order))
                        sys.exit()


            elif extention == "wmd":
                pass
                # file_path_old = os.path.join(OLD_DS_DIR, ds_dir, file)
                # instance_old = MatchingInstance()
                # with open(file_path_old, 'r') as old_file:
                #     instance_old.parse_old(old_file.readlines())
                #
                # file_path = os.path.join(OLD_DS_DIR, ds_dir, file)
                # instance = MatchingInstance(file_path)

