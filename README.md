# PrefLib-Data

This repository contains the data that is available at 
[PrefLib.org](https://preflib.org/>), together with some scripts
we are using to maintain the data.

The most important folder is `datasets` that contains all the datasets. A dataset is represented 
as a directory named `num - abb` where `num` is the series number of the dataset, and `abb` its
abbreviation. Inside a datasets, you will find all the data files and the `info.txt` file. This
folder can be zipped and directly imported in PrefLib. See the 
[PrefLib-Django](https://github.com/PrefLib/PrefLib-Django) repository for more details about that.

The format for the files changed in September 2022. Since this can cause problems for application
developed prior to that date, we still provide the old files in the folder `datasets_old_format`.

Format Specification
====================

A dataset is a folder containing data files, an  `info.txt` file and potentially a `metadata.csv` file.
In the following, we present the specifications that all these files should follow.

Dataset Information File
------------------------

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

Description: <p>The Dublin North, West, and Meath data sets contain a complete record of votes for two separate elections held in Dublin, Ireland in 2002.  The votes were posted <a href="http://www.dublincountyreturningofficer.com/">online</a> but have since been removed.</p> <p> The data sets are not complete, they contain many partial votes over the candidate set.  The North data set contains 43,942 votes over 12 candidates, the West data set contains 29,988 over 9 candidates, and the Meath set contains 64,081 votes over 14 candidates. </p> <p> The Meath data presented here was donated by Jeffrey O'Neill who runs the site <a href="http://www.openstv.org">OpenSTV.org</a>.</p>

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

- **Name**: the name of the dataset.
- **Abbreviation**: the abbreviation of the dataset, it should be a slug string, i.e., it can only contains letters, numbers, underscores or hyphens.
- **Tags**: a list of tags, comma-separated, indicating the tags that apply to the dataset. See [the PrefLib format page](https:preflib.org/format#structure) for more information about the tags.
- **Series Number**: is the series number of the dataset, it is a 5 digit identifier.
- **Publication Date**: the date at which the dataset was publish in the PrefLib system for the first time.
- **Description**: an HTML string that describes the dataset, will be rendered as is in the dataset page in [PrefLib.org](https://preflib.org/).
- **Required Citations**: a list of the required citations that have to be included in every publication making use of the dataset.
- **Selected Studies**: a list of additional references that can be useful.

The second part of the file describes all the data files of the dataset in a csv fashion. We detail 
a bit on the headers in the following.

- **file_name**: the name of the data file.
- **modification_type**: the modification type of the file. See [the PrefLib format page](https:preflib.org/format#metadata) for more information about it.
- **relates_to**: the name of the file that the current file relates to. It would typically be the source file in case the current file has been derived from another one.
- **title**: the title of the data file, e.g., the year of the election it represents.
- **description**: a brief description of the data file if some additional information are needed.
- **publication_date**: the date at which the data file was publish in the PrefLib system for the first time.

Among all those headers, `relates_to` and `description` can be empty. All the others are required.

Note that if a comma should appear in a field (e.g., in `description`), the value of the field should be put into
triple double quotes: `"""this is my description, with a comma."""`. This also mean that triple double quotes
should not be used for any other usage.

Data Files
----------

The most important content of a dataset is the data files it contains. We do not detail the format of those files  here,
but rather refer the reader to [the PrefLib format page](https:preflib.org/format#format) where all the details are
presented. In the following, we provide additional specifications about the data files. Please follow them when
formatting data into the PrefLib format.

- Metadata lines should all be at the start of the files.
- There should not be line break between the metadata and the preferences section of a data file.
- Alternative numbering should start at 1 and not at 0.
- For the data types allowing for multiplicity, the same preference cannot appear twice, the multiplicity is there for that.
- No two alternatives can have the same name.
