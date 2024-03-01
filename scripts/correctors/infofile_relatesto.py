
dataset = "00011 - web"
new_str = ""

original_type = 'soi'
with open("../../datasets/" + dataset + "/info.txt", "r") as file:
    for line in file.readlines():
        line = line.strip()
        if "imbued" in line:
            split = line.split(',')
            new_str += "{},{}, {},{}, {},{}\n".format(split[0], split[1], split[0].split('.')[0] + '.' + original_type, split[3],
                                                      'Obtained from the ' + original_type + ' by adding the unranked alternatives at the bottom', split[5])
        else:
            new_str += line + "\n"

print(new_str)

with open("../../datasets/" + dataset + "/info.txt", "w") as file:
    file.write(new_str)