import os

from preflibtools.instances.preflibinstance import OrdinalInstance


IN_DIR = "../datasets/"

for ds_dir in os.listdir(IN_DIR):
    if os.path.isdir(os.path.join(IN_DIR, ds_dir)):
        if ds_dir in ["pierce", "sf", "sl", "berkley", "aspen", "oakland"]:
            for file in os.listdir(os.path.join(IN_DIR, ds_dir)):
                if os.path.splitext(file)[1] in [".soc", ".toc", ".soi", ".toi"]:
                    file_path = os.path.join(IN_DIR, ds_dir, file)
                    instance = OrdinalInstance()
                    instance.parse_file(file_path, autocorrect=True)

                    positions_to_remove = []
                    for i in range(len(instance.orders)):
                        order = instance.orders[i]
                        alternatives_appearing = [alt for indif_class in order for alt in indif_class]
                        if len(alternatives_appearing) > len(set(alternatives_appearing)):
                            positions_to_remove.append(i)

                    if positions_to_remove:
                        if os.path.splitext(file)[1] == ".toi":
                            os.rename(file_path, os.path.splitext(file_path)[0] + ".dat")
                        positions_to_remove.sort(reverse=True)
                        for pos in positions_to_remove:
                            del instance.orders[pos]
                        instance.recompute_cardinality_param()
                        instance.write(file_path)

