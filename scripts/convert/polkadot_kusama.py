import os

from preflibtools.instances import CategoricalInstance

polkadot_details = {
    "src": "pol_elections",
    "ds_number": "00060",
    "abbreviation": "polkadot",
    "name": "Polkadot Network",
    "publication_date": "26/02/2024"
}
kusama_details = {
    "src": "kur_elections",
    "ds_number": "00061",
    "abbreviation": "kusama",
    "name": "Kusama Network",
    "publication_date": "26/02/2024"
}

for ds_details in [polkadot_details, kusama_details]:
    dataset_dir_path = os.path.join("..", "..", "datasets", ds_details['ds_number'] + " - " + ds_details["abbreviation"])
    os.makedirs(dataset_dir_path, exist_ok=True)
    file_count = 0
    all_files_in_dataset = []

    all_source_files = sorted(os.listdir(ds_details["src"]), key=lambda x: int(x.split(".")[0][3:]))
    for file_name in all_source_files:
        file_count += 1
        print(f"Converting {file_name}")

        instance = CategoricalInstance()
        instance.data_type = "cat"
        instance.modification_type = "original"
        instance.num_categories = 1
        # instance.num_categories = 2
        instance.categories_name = {1: "Approved"}
        # instance.categories_name = {1: "Approved", 2: "Not Approved"}
        instance.title = ""
        instance.description = ""
        instance.publication_date = ds_details["publication_date"]
        instance.modification_date = instance.publication_date

        weights_per_pref = {}
        with open(os.path.join(ds_details["src"], file_name)) as f:
            reading_alternatives = True
            reading_approvals = False
            for line in f.readlines():
                if line.startswith("# "):
                    instance.title = " ".join(line.split(" ")[1].split(".")[0].split("_")[2:4]).title()
                elif reading_alternatives:
                    if line.startswith("## "):
                        reading_alternatives = False
                        reading_approvals = True
                    else:
                        alt_index, alt_name = line.split(",")
                        alt_name = alt_name.strip()
                        alt_index = int(alt_index)
                        instance.alternatives_name[alt_index + 1] = alt_name
                elif reading_approvals:
                    if not line.startswith("%% "):
                        voter_name, voter_weight, voter_ballot = line.split(":")
                        voter_ballot = voter_ballot.strip()
                        if voter_ballot:
                            approved_alts = tuple(int(a.strip()) for a in voter_ballot.split(','))
                            approved = set()
                            not_approved = set()
                            for alternative in instance.alternatives_name:
                                alt_index = alternative - 1
                                if alt_index in approved_alts:
                                    approved.add(alternative)
                                else:
                                    not_approved.add(alternative)
                            approved = tuple(sorted(approved))
                            pref = (approved,)
                            # approved = tuple(sorted(approved))
                            # not_approved = tuple(sorted(not_approved))
                            # pref = (approved, not_approved)
                            if pref in instance.preferences:
                                instance.multiplicity[pref] += 1
                                weights_per_pref[pref].append(voter_weight)
                            else:
                                instance.preferences.append(pref)
                                instance.multiplicity[pref] = 1
                                weights_per_pref[pref] = [voter_weight]
        if file_count < 10:
            file_numbering = "0000000" + str(file_count)
        elif file_count < 100:
            file_numbering = "000000" + str(file_count)
        elif file_count < 1000:
            file_numbering = "00000" + str(file_count)
        else:
            file_numbering = "0000" + str(file_count)
        final_file_name = ds_details["ds_number"] + "-" + file_numbering + ".cat"
        dat_file_name = ds_details["ds_number"] + "-" + file_numbering + ".dat"
        instance.num_alternatives = len(instance.alternatives_name)
        instance.recompute_cardinality_param()
        instance.related_files = dat_file_name
        instance.write(os.path.join(dataset_dir_path, final_file_name))
        all_files_in_dataset.append((final_file_name, instance.modification_type,
                                     instance.relates_to, instance.title, instance.description,
                                     instance.publication_date))

        with open(os.path.join(dataset_dir_path, dat_file_name), "w") as dat_file:
            instance.file_name = dat_file_name
            instance.title += " - Weights"
            instance.description = f"The weights of the ballots described in the file {final_file_name} in the format: ballot: list_of_weights."
            instance.data_type = "dat"
            instance.related_files = ""
            instance.relates_to = final_file_name
            instance.write_metadata(dat_file)
            for pref, weights in weights_per_pref.items():
                pref_str = ""
                for category in pref:
                    if len(category) == 0:
                        pref_str += '{}, '
                    elif len(category) == 1:
                        pref_str += str(category[0]) + ", "
                    else:
                        pref_str += "{" + ", ".join((str(alt) for alt in category)) + "}, "
                dat_file.write("{}: {}\n".format(pref_str.strip(", "), ", ".join(weights)))

        all_files_in_dataset.append((
            dat_file_name,
            instance.modification_type,
            final_file_name,
            instance.title,
            instance.description,
            instance.publication_date
        ))
    with open(os.path.join(dataset_dir_path, "info.txt"), "w", encoding="utf-8") as info_file:
        info_file.write(f"""Name: {ds_details["name"]}

Abbreviation: {ds_details["abbreviation"]}

Tags: Election

Series Number: {ds_details["ds_number"]}

Publication Date: {ds_details["publication_date"]}

Description:

Required Citations: Niclas Boehmer, Markus Brill, Alfonso Cevallos, Jonas Gehrlein, Luis Sánchez-Fernández, and Ulrike Schmidt-Kraepelin. <em>Approval-Based Committee Voting in Practice: A Case Study of (Over-)Representation in the Polkadot Blockchain</em>. AAAI, 2024.

Selected Studies:

file_name, modification_type, relates_to, title, description, publication_date\n""")
        for file_info in all_files_in_dataset:
            info_file.write(", ".join([str(i) if i is not None else '' for i in file_info]) + "\n")

