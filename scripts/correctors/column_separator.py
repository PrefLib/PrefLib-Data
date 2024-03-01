dataset = "00039 - csconf"
datafile = "00039-00000003.cat"

new_str = ""
with open("../../datasets/" + dataset + "/" + datafile, "r") as file:
    for line in file.readlines():
        if line.startswith("#"):
            new_str += line
        else:
            split = line.split(',')
            new_str += split[0] + ': '
            new_str += ','.join(split[1:])

with open("../../datasets/" + dataset + "/" + datafile, "w") as file:
    file.write(new_str)
