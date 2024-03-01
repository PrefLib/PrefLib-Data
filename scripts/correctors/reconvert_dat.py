import os.path
from preflibtools.instances.preflibinstance import OrdinalInstance

dataset = "00022 - sl"
original_type = '.toi'

for file in os.listdir(os.path.join("..", "..", "datasets", dataset)):
    if os.path.splitext(file)[1] == ".dat":
        new_str = ""
        with open(os.path.join("..", "..", "datasets", dataset, file)) as old_file:
            with open(os.path.join("..", "..", "datasets", dataset, os.path.splitext(file)[0] + original_type)) as related_file:
                instance = OrdinalInstance()
                lines_old = old_file.readlines()
                instance.parse_old(lines_old)
                for line in related_file.readlines():
                    if line.startswith('#'):
                        if line.startswith("# FILE NAME"):
                            new_str += line.strip()[:-3] + "dat\n"
                        elif line.startswith("# DATA TYPE"):
                            new_str += line.strip()[:-3] + "dat\n"
                        elif line.startswith("# DESCRIPTION"):
                            new_str += line.strip() + " Includes the invalid ballots\n"
                        elif line.startswith("# RELATES TO"):
                            new_str += line.strip() + " " + os.path.splitext(file)[0] + original_type + "\n"
                        elif line.startswith("# RELATED FILES"):
                            new_str += "# RELATED FILES:\n"
                        elif line.startswith("# NUMBER VOTERS"):
                            new_str += "# NUMBER VOTERS: " + str(sum(instance.multiplicity.values())) + "\n"
                        elif line.startswith("# NUMBER UNIQUE ORDERS"):
                            new_str += "# NUMBER UNIQUE ORDERS: " + str(len(instance.orders)) + "\n"
                        else:
                            new_str += line
                    else:
                        break
                for line in lines_old[instance.num_alternatives + 2:]:
                    split = line.split(',')
                    new_str += split[0] + ': '
                    new_str += ','.join(split[1:])
                print(new_str)

        with open(os.path.join("..", "..", "datasets", dataset, file), "w") as new_file:
            new_file.write(new_str)
