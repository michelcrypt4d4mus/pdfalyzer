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
from pdfalyzer.helpers.dict_helper import flatten
from pdfalyzer.helpers.filesystem_helper import file_size_in_mb
from pdfalyzer.output.layout import print_section_subheader, _print_header_panel
from pdfalyzer.pdfalyzer import Pdfalyzer

PYPDF_REPO_DIR = Path("../pypdf")
PYPDF_RESOURCES_DIR = PYPDF_REPO_DIR.joinpath('resources')
PYPDF_ENCRYPTED_DIR = PYPDF_RESOURCES_DIR.joinpath('encyrpted')
PYPDF_SAMPLES_DIR = PYPDF_REPO_DIR.joinpath('sample-files')
PYPDF_CACHE_DIR = PYPDF_REPO_DIR.joinpath('tests', 'pdf_cache')
PICKLED_PATH = Path('./count_fonts_in_pypdf_samples.pkl.gz')

PDF_DIRS = [
    PYPDF_RESOURCES_DIR,
    PYPDF_SAMPLES_DIR,
    PYPDF_CACHE_DIR,  # Wonky PDFs
]

SLOW_PDFS = [
    'issue-604.pdf',
    'iss_1134.pdf',
    'iss2963.pdf',
    'test_write_outline_item_on_page_fitv.pdf',
    'LegIndex-page6.pdf',
]


files = [f for f in flatten([dir.glob('*.pdf') for dir in PDF_DIRS]) if '_img' not in str(f)]
file_fonts: dict[str, list[FontInfo]] = {}

for file in files:
    if file.name in SLOW_PDFS:
        continue

    console.line()
    file_key = str(file).removeprefix(str(PYPDF_REPO_DIR) + '/')
    panel_txt = Text('pdfalyzing ').append(f"{file}", 'bright_cyan').append(f" ({file_size_in_mb(file)} MB)", style='dim')
    _print_header_panel(panel_txt, 'grey50', False, 100, internal_padding=(1,4))

    try:
        pdfalyzer = Pdfalyzer(file, 'password')
        file_fonts[file_key] = pdfalyzer.font_infos
        font_names = [f"{fi.display_title}: {unique_font_string(fi.font_obj)}" for fi in pdfalyzer.font_infos]
        console.print(f"    -> Found {len(font_names)} FontInfos", style='bright_green bold')

        for i, name in enumerate(font_names, 1):
            console.print(f"        - {name}", style='cyan')
    except Exception as e:
        console.print_exception()
        log.error(f"Error processing '{file}': {type(e).__name__} ({e})")

console.line(5)

for file in sorted(file_fonts.keys(), key=lambda f: -1 if isinstance(f, str) else len(file_fonts[f])):
    console.line()
    font_infos = file_fonts[file]
    console.print(Text('').append(file, style='bright_green bold').append(f" has {len(font_infos)} FontInfos"))

    for i, fi in enumerate(font_infos):
        txt = Text(f'        [{i}] ', style='grey27').append(fi.display_title, style='bright_cyan')
        console.print(txt.append(': ').append(unique_font_string(fi.font_obj), style='dim'))


# with gzip.open(PICKLED_PATH, 'wb') as file:
#     for font_list in file_fonts.values():
#         if isinstance(font_list, list):
#             for font in font_list:
#                 font.binary_scanner = None  # has to be removed to pickle successfully

#     pickle.dump(file_fonts, file)
#     print(f"Pickled data to '{PICKLED_PATH}' ({file_size_in_mb(PICKLED_PATH)} MB)...")
