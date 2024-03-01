from preflibtools.instances import CategoricalInstance

instance = CategoricalInstance()
instance.file_name = "00037-00000003.cat"
instance.data_type = "cat"
instance.modification_type = "original"
instance.related_files = ["00037-00000003.csv"]
instance.title = "AAMAS 2021"
instance.description = "Bidding data for the conference AAMAS 2021"
instance.publication_date = "2023-07-04"
instance.modification_date = "2023-07-04"

categories = ["yes", "maybe", "no", "conflict"]
instance.num_categories = len(categories)
instance.categories_name = {1: "yes", 2: "maybe", 3: "no", 4: "conflict"}

with open("../../datasets/00037 - aamas/00037-00000003.csv") as csv_file:
    bids_per_bidder = dict()
    for line in csv_file.readlines():
        if line.startswith("spc") or line.startswith("pc"):
            bidder, paper, bid = line.strip().split(",")
            if bidder not in bids_per_bidder:
                bids_per_bidder[bidder] = dict()
                for cat in categories:
                    bids_per_bidder[bidder][cat] = []
            bids_per_bidder[bidder][bid].append(paper)

alternatives = set()
for bids in bids_per_bidder.values():
    for paper_list in bids.values():
        alternatives.update(paper_list)

for bidder, bids in bids_per_bidder.items():
    selected_alts = set()
    selected_alts.update(bids["yes"])
    selected_alts.update(bids["maybe"])
    selected_alts.update(bids["conflict"])
    for alt in alternatives:
        if alt not in selected_alts:
            bids["no"].append(alt)

for bidder, bids in bids_per_bidder.items():
    pref = (tuple(bids["yes"]), tuple(bids["maybe"]), tuple(bids["no"]), tuple(bids["conflict"]))
    if pref in instance.multiplicity:
        instance.multiplicity[pref] += 1
    else:
        instance.multiplicity[pref] = 1
    instance.preferences.append(pref)


alternatives = list(alternatives)
alternatives.sort(key=int)

instance.num_alternatives = len(alternatives)
for alt in alternatives:
    instance.alternatives_name[alt] = "Anon Paper " + str(alt)


instance.recompute_cardinality_param()

instance.write("../../datasets/00037 - aamas/00037-00000003.cat")
