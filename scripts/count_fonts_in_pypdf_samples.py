#!/usr/bin/env python
import gzip
import json
import pickle
import re
from collections import defaultdict
from pathlib import Path

from rich.text import Text
from yaralyzer.output.rich_console import console
from yaralyzer.util.logging import log

from pdfalyzer.font_info import FontInfo, unique_font_string
from pdfalyzer.helpers.filesystem_helper import file_size_in_mb
from pdfalyzer.output.layout import print_section_subheader
from pdfalyzer.pdfalyzer import Pdfalyzer

PYPDF_REPO_DIR = Path("../pypdf")
PYPDF_RESOURCES_DIR = PYPDF_REPO_DIR.joinpath('resources')
PYPDF_ENCRYPTED_DIR = PYPDF_RESOURCES_DIR.joinpath('encyrpted')
PYPDF_SAMPLES_DIR = PYPDF_REPO_DIR.joinpath('sample-files')
PICKLED_PATH = Path('./count_fonts_in_pypdf_samples.pkl.gz')


file_fonts: dict[str, list[FontInfo]] = {}

for file in PYPDF_RESOURCES_DIR.glob('*.pdf'):
    file_key = str(file).removeprefix(str(PYPDF_REPO_DIR) + '/')
    print_section_subheader(f"pdfalyzing '{file}'...")

    try:
        pdfalyzer = Pdfalyzer(file)
        file_fonts[file_key] = pdfalyzer.font_infos
        font_names = [f"{fi.display_title}: {unique_font_string(fi.font_obj)}" for fi in pdfalyzer.font_infos]
        console.print(f"\n    -> Found {len(font_names)} FontInfos", style='bright_green bold')

        for i, name in enumerate(font_names, 1):
            console.print(f"        - {name}", style='cyan')
    except Exception as e:
        console.print_exception()
        log.error(f"Error processing '{file}': {type(e).__name__} ({e})")


for file in sorted(file_fonts.keys(), key=lambda f: -1 if isinstance(f, str) else len(file_fonts[f])):
    font_infos = file_fonts[file]
    console.line()
    console.print(Text('').append(file, style='bright_green bold').append(f"has {len(font_infos)} FontInfos"))

    for fi in font_infos:
        font_name = f"{fi.display_title}: {unique_font_string(fi.font_obj)}"
        console.print(Text(f'        [{i}]', style='grey27').append(font_name, style='cyan'))


# with gzip.open(PICKLED_PATH, 'wb') as file:
#     for font_list in file_fonts.values():
#         if isinstance(font_list, list):
#             for font in font_list:
#                 font.binary_scanner = None  # has to be removed to pickle successfully

#     pickle.dump(file_fonts, file)
#     print(f"Pickled data to '{PICKLED_PATH}' ({file_size_in_mb(PICKLED_PATH)} MB)...")
