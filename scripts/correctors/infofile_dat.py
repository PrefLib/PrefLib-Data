
dataset = "kidney"
new_str = ""
with open("../../datasets/" + dataset + "/info.txt", "r") as file:
    for line in file.readlines():
        line = line.strip()
        if ".dat" in line:
            split = line.split(',')
            new_str += "{},{}, {},{}, {},{}\n".format(split[0], split[1], split[0].split('.')[0] + '.wmd', split[3], 'Extra information about the wmd file', split[5])
        else:
            new_str += line + "\n"

print(new_str)

with open("../../datasets/" + dataset + "/info.txt", "w") as file:
    file.write(new_str)