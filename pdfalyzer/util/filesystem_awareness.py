"""
A resource all the project code can use to understand the file system and this project's
place in it
"""
from os import path
import pathlib


PROJECT_DIR = path.realpath(path.join(pathlib.Path(__file__).parent.resolve(), '..', '..'))

DOCUMENTATION_DIR = path.join(PROJECT_DIR, 'doc')
SVG_DIR = path.join(DOCUMENTATION_DIR, 'svgs')
RENDERED_IMAGES_DIR = path.join(SVG_DIR, 'rendered_images')

YARA_RULES_DIR = path.join(PROJECT_DIR, 'yara')
