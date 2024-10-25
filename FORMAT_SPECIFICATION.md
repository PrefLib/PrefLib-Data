# Format Specification

This is the full specification of the PrefLib data format. The following should be considered 
the reference text and the different implementation of the PrefLib ecosystem should follow this
specification.

Links:
- [Datasets](#datasets)
  - [Dataset `info.txt`](#dataset-infotxt)
- [Data files](#datafiles)
  - [Data Types](#data-types)
  - [PrefLib File Format](#preflib-file-format)
    - [Metadata Header](#metadata-header)
    - [Modification Type](#modification-type)
    - [File Formats for Ordinal Preferences](#file-formats-for-ordinal-preferences)
    - [File Format for Categorical Preferences](#file-format-for-categorical-preferences)
    - [File Format for Weighted Matching](#file-format-for-weighted-matching)
    - [Extra Data File](#extra-data-file)

## Datasets

A dataset is a (zipped) folder containing data files, an  `info.txt` file and potentially a 
`metadata.csv` file. The name of the folder is typically `num - abb` where `num` is the series 
number of the dataset, and `abb` its abbreviation.

### Dataset `info.txt`

Every dataset must include an `info.txt` file. It contains two sections. The first section presents
a set of metadata about the dataset, encoded in the format `MetadataName: Value`. The second session
describes the data files of the dataset. Its format follows that of a csv file, with comma separator.

Here is an example of the file, taken from the irish dataset.

```text
Name: Irish Election Data

Abbreviation: irish

Tags: Election

Series Number: 00001

Publication Date: 2013-08-17

Description: <p>The Dublin North, West, and Meath data sets contain a complete record of votes...</p>

Required Citations:

Selected Studies: Budgeted Social Choice: From Consensus to Personalized Decision Making; Tyler Lu and Craig Boutilier; Proceedings of IJCAI; 2011

file_name, modification_type, relates_to, title, description, publication_date
00001-00000001.soi, original, , 2002 Dublin North, , 2013-08-17
00001-00000001.toc, imbued, 00001-00000001.soi, 2002 Dublin North, Obtained from the soi by adding the unranked alternatives at the bottom, 2013-08-17
00001-00000002.soi, original, , 2002 Dublin West, , 2013-08-17
00001-00000002.toc, imbued, 00001-00000002.soi, 2002 Dublin West, Obtained from the soi by adding the unranked alternatives at the bottom, 2013-08-17
00001-00000003.soi, original, , 2002 Meath, , 2013-08-17
00001-00000003.toc, imbued, 00001-00000003.soi, 2002 Meath, Obtained from the soi by adding the unranked alternatives at the bottom, 2013-08-17
```

Let us describe in more details the metadata:

- *Name*: The name of the dataset.
- *Abbreviation*: The abbreviation of the dataset, it should be a slug string, i.e., it can only contains letters, numbers, underscores or hyphens.
- *Tags*: A list of tags, comma-separated, indicating the tags that apply to the dataset.
- *Series Number*: A unique identifier formatted as a 5-digit, zero-padded integer. The series begins with "00001" and increments by 1 for each subsequent entry, e.g., "00001", "00002", "00003", etc.
- *Publication Date*: The date at which the dataset was publish in the PrefLib ecosystem for the first time.
- *Description*: An HTML string that describes the dataset. This field will be rendered as is on the website [PrefLib.org](https://preflib.org/).
- *Required Citations*: A list of the required citations that have to be included in every publication making use of the dataset.
- *Selected Studies*: A list of additional references that can be useful to the users of the dataset.

All these metadata are mandatory. The value should be blank if there is no information for a given metadata.

The second part of the file describes all the data files of the dataset in a csv fashion. We detail 
the headers in the following.

- *file_name*: The name of the data file.
- *modification_type*: The modification type of the file. See below for more information on the modification type.
- *relates_to*: The name of the file that the current file relates to. It would typically be the source file in case the current file has been derived from another one. Note that files with a relates_to attribute may be displayed less prominently than others (because the source file matters more than the imbued file).
- *title*: The title of the data file, e.g., the year of the election it represents.
- *description*: A brief description of the data file if some additional information are needed. This is typically left empty unless the `relates_to` field is used.
- *publication_date*: The date at which the data file was publish in the PrefLib ecosystem for the first time.

Among all those headers, `relates_to` and `description` can be empty. All the others are required to have a value.

Note that if a comma should appear in a field (e.g., in `description`), the value of the field should be put into
triple double quotes: `"""this is my description, with a comma."""`. This also mean that triple quotes
should not be used for any other usage.

### Dataset Tags

Dataset tags are used to classify datasets based on their characteristics. These are the
tags currently in use.

- *Combinatorial*: The data represent combinatorial preferences over the alternatives.
- *Election*: The preferences apply to a scenario in which some alternatives are to be selected/elected.
- *Experiment*: The datafiles were collected as part of an experiment.
- *Matching*: The preferences apply to a scenario in which alternatives are to be matched to one another.
- *Mturk*: The preferences were collected on Amazon Mechanical Turk.
- *Politics*: The preferences apply to a political scenario.
- *Ratings*: The preferences express ratings about the alternatives.
- *Sport*: The data represent sport events, interpreted as elections.
- *STV*: STV (single-transferable vote) was the voting rule used for the selection of the winner.

This list is not fixed. Extra tags can be added and current tags can be removed.

## Data Files

A data file can be any type of file included in a dataset. Several file formats have been defined 
for the PrefLib ecosystem. These formats should be preferred over other file formats but it is not
mandatory to use them.

### Data Types

The PrefLib ecosystem defines 6 different data types.

- *Strict Orders Complete (SOC)*: The SOC extension contains preferences represented by a strict and complete linear order (transitive, and asymmetric relation) over the alternatives. They are complete in the sense that every linear order contains the whole set of alternatives. They are strict in the sense that no two alternatives can be tied.
- *Strict Orders Incomplete (SOI)*: The SOI extension contains preferences represented by a strict and possibly incomplete linear order (transitive, and asymmetric relation) over the alternatives. They are possibly incomplete in the sense that some preferences might not contain the whole set of alternatives. They are strict in the sense that no two alternatives can be tied.
- *Tie Orders Complete (TOC)*: The TOC extension contains preferences represented by a transitive and complete relation over the alternatives. They are complete in the sense that every preference contains the whole set of candidates. They need not be strict: several alternatives can be tied.
- *Tie Orders Incomplete (TOI)*: The TOI extension contains preferences represented by a transitive and possibly incomplete relation over the alternatives. They are possibly incomplete in the sense that some preferences might not contain the whole set of alternatives. They also need not be strict: several alternatives can be tied.
- *Categorical Preferences (CAT)*: Files with a CAT extension describe categorical preferences. In this domain, voters are asked to organise the alternatives into pre-determined categories, for instance the categories “Yes”, “Maybe”, and “No”. There exists an underlying ranking over the categories that determine the voters' preferences. Not all alternatives have to be categorised and some categories can be left empty.
- *Weighted Matching Data (WMD)*: Files with a WMD extension describe a set of weighted matching data. These are weighted directed graphs, i.e., a collection of edges between the alternatives associated with a weight. 

### PrefLib File Format

For each of the data type defined above, a corresponding file format has been defined.
All the data file share a common file format, with few adaptions for each specific type.

Data files contain two sections, first a list of metadata with lines starting with a “#”;
second the preference data itself.

#### Metadata Header

We start with an example of a file header.

```text
# FILE NAME: 00001-00000001.soi
# TITLE: 2002 Dublin North
# DESCRIPTION: 
# DATA TYPE: soi
# MODIFICATION TYPE: original
# RELATES TO: 
# RELATED FILES: 00001-00000001.toc
# PUBLICATION DATE: 2013-08-17
# MODIFICATION DATE: 2022-09-16
# NUMBER ALTERNATIVES: 12
# NUMBER VOTERS: 43942
# NUMBER UNIQUE ORDERS: 19299
# ALTERNATIVE NAME 1: Cathal Boland F.G.
# ALTERNATIVE NAME 2: Clare Daly S.P.
# ALTERNATIVE NAME 3: Mick Davis S.F.
# ALTERNATIVE NAME 4: Jim Glennon F.F.
# ALTERNATIVE NAME 5: Ciaran Goulding Non-P
# ALTERNATIVE NAME 6: Michael Kennedy F.F.
# ALTERNATIVE NAME 7: Nora Owen F.G.
# ALTERNATIVE NAME 8: Eamonn Quinn Non-P
# ALTERNATIVE NAME 9: Sean Ryan Lab
# ALTERNATIVE NAME 10: Trevor Sargent G.P.
# ALTERNATIVE NAME 11: David Henry Walshe C.C. Csp
# ALTERNATIVE NAME 12: G.V. Wright F.F.
```

We now describe each of the metadata of the example header.

- FILE NAME: The name of the file.
- TITLE: The title of the data file, for instance the year of the election represented in the data file.
- DESCRIPTION: A description of the data file, providing additional information about it. This is typically left empty.
- DATA TYPE: The type of the data in the data file as described above.
- MODIFICATION TYPE: The modification type of the data file as described below.
- RELATES TO: The name of the data file that the current file relates to, typically the source file in case the current file has been derived from another one.
- RELATED FILES: The list of all the data files related to this one, comma separated.
- PUBLICATION DATE: The date at which the data file was publish in the PrefLib system for the first time.
- MODIFICATION DATE: The last time the data file was modified.
- NUMBER ALTERNATIVES: The number of alternatives in the data file (not all of them have to appear in the preferences).
- ALTERNATIVE NAME X: The name of alternative number X.

Whichever the file format, all these metadata have to be present. Additional metadata 
that are specific to the file can then be added.

Here are some general formatting rules:
- Metadata lines should all be at the start of the files.
- There should not be line break between the metadata and the preferences section of a data file.
- Alternative numbering should start at 1 and not at 0.
- No two alternatives can have the same name.

#### Modification Type

Each data file is labeled as either Original, Induced, Imbued or Synthetic.

- *Original*: Data that has only been converted into our formatting.
- *Induced*: Data that has been induced from another context. For example, computing a pairwise relation from a set of strict total orders. No assumptions have been made to create these files, just a change in the expression language.
- *Imbued*: Data that has been imbued with extra information. For example, extending an incomplete partial order by placing all unranked candidates tied at the end.
- *Synthetic*: Data that has been generated artificially. It is for example, instances of the kidney matching problem generated via the art donor pool generation method.

#### File Formats for Ordinal Preferences

The file formats for ordinal preferences are SOC, SOI, TOC, TOI.
These four file formats are very similar: the metadata header has the same specification, the 
description of the preference differs.

##### Metadata Header

In addition to the metadata described above, the header of files representing ordinal preferences
also include the following metadata.

- NUMBER VOTERS: the number of voters who submitted an order.
- NUMBER UNIQUE ORDERS: the number unique orders that have been submitted.

##### Preferences

The preferences submitted by the respondents are encoded as described in the following. 
Each line indicates first the number of voters who submitted the given preference list, and then,
after a column, the preference list. Inside a preference list, a strict ordering is indicated by
comma, and indifference classes are grouped within curly brackets. Preferences are transitive.

We provide below two examples of this encoding:
    - `1: 1, 4, 3, 2`: 1 respondent submitted the following preferences: alternative 1 is preferred to alternative 4, that is preferred to alternative 3, itself preferred to alternative 2. 
    - `13: 1, {4, 3}, 2`: 13 respondent submitted the following preferences: alternative 1 is preferred to alternatives 4 and 3, that are both preferred to alternative 2, but alternatives 4 and 3 are ranked at the same position.

Each file format has specific constraints as to which orders can appear:
- For SOC files all the alternatives should appear in the orders and ties are not allowed. 
- For SOI files ties are not allowed and it is not mandatory that all alternatives appear in the orders.
- For TOC files all the alternatives should appear in the orders and ties are allowed.
- For TOI files ties are allowed and it is not mandatory that all alternatives appear in the orders.

It is mandatory that each file uses the most restrictive file format that is compatible with the preferences.
So even though an SOC file can also be formatted as a TOI file, the SOC file format should be used.

It is mandatory that no orders appears more than once, the multiplicity value for each order is used for that.

To conclude, here is an example of the first lines of a data file of complete orders with ties (TOC) (taken from the debian election dataset).
```text
# FILE NAME: 00002-00000001.toc
# TITLE: Debian 2002 Leader
# DESCRIPTION: Obtained from the soi by adding the unranked alternatives at the bottom
# DATA TYPE: toc
# MODIFICATION TYPE: imbued
# RELATES TO: 00002-00000001.soi
# RELATED FILES:
# PUBLICATION DATE: 2013-08-17
# MODIFICATION DATE: 2022-09-16
# NUMBER ALTERNATIVES: 4
# NUMBER VOTERS: 475
# NUMBER UNIQUE ORDERS: 31
# ALTERNATIVE NAME 1: Branden Robinson
# ALTERNATIVE NAME 2: Raphael Hertzog
# ALTERNATIVE NAME 3: Bdale Garbee
# ALTERNATIVE NAME 4: None Of The Above
100: 3,1,2,4
79: 1,3,2,4
54: 3,2,1,4
43: 2,3,1,4
34: 3,2,4,1
30: 1,2,3,4
29: 2,1,3,4
16: 1,3,4,2
14: 2,3,4,1
12: 3,1,4,2
9: 3,{1,2,4}
```

#### File Format for Categorical Preferences

The file format for categorical preferences is CAT.

##### Metadata Header

In addition to the metadata described above, the header of files representing categorical preferences
also include the following metadata.

- NUMBER VOTERS: The number of voters who submitted their preference.
- NUMBER UNIQUE PREFERENCES: The number unique preferences that have been submitted.
- NUMBER CATEGORIES: The number of categories the voters were asked to put alternatives in.
- CATEGORY NAME X: The name of category number X.

##### Preferences

The preferences submitted by the respondents are encoded as described in the following. 
Each line indicates first the number of voters who submitted the given preference list, and then, 
after a column, the preference list. Inside a preference list, each category is grouped around 
curly brackets, except for the categories with a single alternative. The empty category is represented as "{}". 

We provide below two examples of this encoding:
- `1: 1, 3, {}`: 1 respondent submitted the following preferences: alternative 1 is in category 1, alternative 3 in the second category, and the last category is left empty.
- `86: {}, 1, {2, 3}`: 86 respondents submitted the following preferences: the first category is empty, alternative 1 is in the second category and alternatives 2 and 3 are in the last category.

It is mandatory that no preference appears more than once, the multiplicity value for each preference is used for that.

To conclude, here is an example of the first lines of a CAT file from the French Approval dataset.
```text
# FILE NAME: 00026-00000001.cat
# TITLE: GylesNonains
# DESCRIPTION:
# DATA TYPE: cat
# MODIFICATION TYPE: original
# RELATES TO:
# RELATED FILES: 00026-00000001.toc
# PUBLICATION DATE: 2017-04-13
# MODIFICATION DATE: 2022-09-16
# NUMBER ALTERNATIVES: 16
# NUMBER VOTERS: 365
# NUMBER UNIQUE PREFERENCES: 216
# NUMBER CATEGORIES: 2
# CATEGORY NAME 1: Yes
# CATEGORY NAME 2: No
# ALTERNATIVE NAME 1: Megret
# ALTERNATIVE NAME 2: Lepage
# ALTERNATIVE NAME 3: Gluckstein
... 	
13: 6,{1,2,3,4,5,7,8,9,10,11,12,13,14,15,16}
13: {},{1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16}
10: {9,10},{1,2,3,4,5,6,7,8,11,12,13,14,15,16}
10: {1,6},{2,3,4,5,7,8,9,10,11,12,13,14,15,16}
```

#### File Format for Weighted Matching

The file format for weighted matching preferences is WMD.

##### Metadata Header

In addition to the metadata described above, the header of files representing weighted matching
preferences also include the following metadata.

- NUMBER EDGES: The number of edges in the matching graph.

##### Preferences

The preferences submitted by the respondents are encoded as described in the following. The preferences
are viewed as a matching graph. The matching graph is described as a list of Source, Destination, Weight.

Here is an example of the first lines of a WMD file from the Kidney dataset
```text
# FILE NAME: 00036-00000001.wmd
# TITLE: Kidney Matching - 16 with 0
# DESCRIPTION:
# DATA TYPE: wmd
# MODIFICATION TYPE: synthetic
# RELATES TO:
# RELATED FILES: 00036-00000001.dat
# PUBLICATION DATE: 2017-04-13
# MODIFICATION DATE: 2022-09-16
# NUMBER ALTERNATIVES: 16
# NUMBER VOTERS: 365
# NUMBER EDGES: 59
# ALTERNATIVE NAME 1: Pair 1
# ALTERNATIVE NAME 2: Pair 2
# ALTERNATIVE NAME 3: Pair 3
... 	
1,5,1.0
1,6,1.0
2,1,1.0
2,3,1.0
```

#### Extra Data File

When miscellaneous data are needed, we use the file extension DAT which has no specified format. 
CSV files are also sometimes used.
