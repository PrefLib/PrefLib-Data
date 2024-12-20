# PrefLib-Data

This repository contains the data that is available at 
[PrefLib.org](https://preflib.org/>), together with some scripts
we are using to maintain the data.

## Format specification

The format specification for the PrefLib ecosystem is described in
[FORMAT_SPECIFICATION.md](https://github.com/PrefLib/PrefLib-Data/blob/main/FORMAT_SPECIFICATION.md).
A rendered version is available at [preflib.org/format](https://preflib.org/format)

### Old file format

The format for the files changed in September 2022. Since this can cause problems for application
developed prior to that date, we still provide the old files in the folder `datasets_old_format`.

## How To

### Add/modify a dataset

Follow these steps:

1. Create the corresponding folder in the `datasets/` folder. The name should be `{number} - {abb}` where `number` is the series number of the dataset and `abb` its abbreviation.
2. Move the files to the folder. This should include data files and an `info.txt` file. They should respect the format specification.
3. Run the sanity checks: the script is `scripts/sanitychecks.py` (this is also done automatically via GitHub actions on every push).
4. Generate the metadata file: the script is `scripts/compute_metadata.py`. You can also do that by running the [Generate the metadata.csv files](https://github.com/PrefLib/PrefLib-Data/actions/workflows/metdata.yml) GitHub action (click on "Run workflow").
5. Push to the changes to GitHub repository.
6. Update the ZIP archives on the repo via the action [Generate and Upload Zip Files](https://github.com/PrefLib/PrefLib-Data/actions/workflows/releasezip.yml) (see [below](#update-the-zip-archives) for more details).
7. Zip the new/modified dataset using the script `scripts/zipall.py`.
8. Update the website with the zip file as explained in the repository [PrefLib-Jekyll](https://github.com/PrefLib/PrefLib-Jekyll).

If the data has been added via a pull request, you do not need to clone the repo. You can simply merge the PR; wait for the sanity checks to run; compute the metadata via the GitHub action; update the zip in the release via the GitHub action; and you're done. Then, move to [PrefLib-Jekyll](https://github.com/PrefLib/PrefLib-Jekyll) to update the website.

### Update the zip archives

The zip files served from the website are actually hosted as assets of the v1.0 release of this repository.
Whenever the datasets have been modified, or new datasets have been added, the zip files need to be
re-generated.

To do so, go to the [Generate and Upload Zip Files](https://github.com/PrefLib/PrefLib-Data/actions/workflows/releasezip.yml)
action and run the workflow. The zip files from the release will slowly be updated (the process takes around 20 minutes).

**Important**: For this process to work, there needs to be a release with tag `v1.0`. If this release
were to be deleted, re-create it ([here](https://github.com/PrefLib/PrefLib-Data/releases/new))
before running the workflow.
