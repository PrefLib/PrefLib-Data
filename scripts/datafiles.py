"""Helpers for data files that are stored gzip-compressed in the repository.

A data file larger than GitHub comfortably handles (see README) may be stored
as ``<name>.gz``, for instance ``00080-00000005.soi.gz``. Everywhere else it is
known by its plain name: ``info.txt`` and ``metadata.csv`` list
``00080-00000005.soi``, the MD5 in ``metadata.csv`` is that of the plain file,
and ``zipall.py`` writes the plain file into the release zips. Users of the
zips and of the website never see the compressed form.
"""

import gzip
import hashlib
import os
import shutil
import tempfile

from preflibtools.instances import get_parsed_instance

COMPRESSED_SUFFIX = ".gz"


def logical_name(file_name):
    """The plain name of a data file: ``x.soi.gz`` -> ``x.soi``."""
    if file_name.endswith(COMPRESSED_SUFFIX):
        return file_name[: -len(COMPRESSED_SUFFIX)]
    return file_name


def stored_path(file_path):
    """The path on disk of a data file given by its plain or stored path."""
    if os.path.exists(file_path):
        return file_path
    compressed = file_path + COMPRESSED_SUFFIX
    if os.path.exists(compressed):
        return compressed
    return file_path


def open_data_file(file_path):
    """Open a data file (plain or compressed) for binary reading."""
    path = stored_path(file_path)
    if path.endswith(COMPRESSED_SUFFIX):
        return gzip.open(path, "rb")
    return open(path, "rb")


def md5(file_path):
    """MD5 of the plain contents of a data file."""
    hash_md5 = hashlib.md5()
    with open_data_file(file_path) as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def parse_instance(file_path, **kwargs):
    """Parse a data file (plain or compressed) with preflibtools.

    preflibtools infers the data type from the extension and records the file
    name, so a compressed file is decompressed under its plain name first.
    """
    path = stored_path(file_path)
    if not path.endswith(COMPRESSED_SUFFIX):
        return get_parsed_instance(path, **kwargs)
    with tempfile.TemporaryDirectory() as tmp:
        plain = os.path.join(tmp, logical_name(os.path.basename(path)))
        with gzip.open(path, "rb") as src, open(plain, "wb") as dst:
            shutil.copyfileobj(src, dst)
        return get_parsed_instance(plain, **kwargs)
