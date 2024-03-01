

new_lines = []
for j in range(2, 8):
    with open("../../datasets/00035 - breakfast/00035-0000000" + str(j) + ".soc") as file:
        lines = file.readlines()
        file.close()
        if len(new_lines) == 0:
            new_lines.append("00035-0000000" + str(j) + ".soc")
        else:
            new_lines[0] += ";00035-0000000" + str(j) + ".soc"
        if len(new_lines) == 1:
            new_lines.append(lines[1][9:].strip())
        else:
            new_lines[1] +=";" + lines[1][9:].strip()
        lines = lines[28:]
        for j in range(len(lines)):
            if len(new_lines) <= j + 2:
                new_lines.append(lines[j].strip())
            else:
                new_lines[j + 2] += ";" + lines[j].strip()

print(new_lines)
with open("../../datasets/00035 - breakfast/00035-00000001.csv", "w") as file:
    file.write('\n'.join(new_lines))
