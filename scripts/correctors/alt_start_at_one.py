import os.path

from preflibtools.instances.preflibinstance import OrdinalInstance, CategoricalInstance


dataset = "00036 - kidney"

for file in os.listdir(os.path.join("..", "..", "datasets", dataset)):
    print(file)
    extension = os.path.splitext(file)[1][1:]
    if extension in ["soc", "soi", "toc", "toi"]:
        print(file)
        instance = OrdinalInstance(os.path.join("..", "..", "datasets", dataset, file))

        alt_zero_appears = False
        for order in instance.orders:
            for indif_class in order:
                if 0 in indif_class:
                    alt_zero_appears = True
                    break
            if alt_zero_appears:
                break
        if alt_zero_appears:
            new_instance = OrdinalInstance(os.path.join("..", "..", "datasets", dataset, file))
            new_instance.orders = []
            new_instance.multiplicity = {}
            for order in instance.orders:
                new_order = tuple(tuple(alt + 1 for alt in indif_class) for indif_class in order)
                new_instance.orders.append(new_order)
                new_instance.multiplicity[new_order] = instance.multiplicity[order]
            new_instance.write(os.path.join("..", "..", "datasets", dataset, file))

    elif extension == "cat":
        instance = CategoricalInstance(os.path.join("..", "..", "datasets", dataset, file))

        alt_zero_appears = False
        for pref in instance.preferences:
            for category in pref:
                if 0 in category:
                    alt_zero_appears = True
                    break
            if alt_zero_appears:
                break
        if alt_zero_appears:
            new_instance = CategoricalInstance(os.path.join("..", "..", "datasets", dataset, file))
            new_instance.preferences = []
            new_instance.multiplicity = {}
            for pref in instance.preferences:
                new_pref = tuple(tuple(alt + 1 for alt in category) for category in pref)
                new_instance.preferences.append(new_pref)
                new_instance.multiplicity[new_pref] = instance.multiplicity[pref]
            new_instance.write(os.path.join("..", "..", "datasets", dataset, file))

    elif extension == "wmd":
        new_str = ""
        with open(os.path.join("..", "..", "datasets", dataset, file)) as f:
            for line in f.readlines():
                if line.startswith('#'):
                    new_str += line
                else:
                    split = line.split(',')
                    new_str += "{},{},{}".format(int(split[0]) + 1, int(split[1]) + 1, split[2])
        print(new_str)
        with open(os.path.join("..", "..", "datasets", dataset, file), "w") as f:
            f.write(new_str)
