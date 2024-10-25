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
